from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import Enum
from pathlib import Path
from threading import Thread, Lock, Event
from typing import Dict, List, Optional, Union, Callable
import json
import logging
import os
import schedule
import threading
import time as time_module
from TTS import Voicepods

class RepeatType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    ONCE = "once"
    CUSTOM = "custom"  # New type for custom intervals

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AlarmData:
    time: datetime
    message: str
    enabled: bool = True
    priority: Priority = Priority.MEDIUM
    snooze_count: int = 0
    max_snooze: int = 3
    snooze_interval: int = 5  # minutes
    tags: List[str] = None

@dataclass
class ScheduleData:
    time: time
    message: str
    repeat: RepeatType
    enabled: bool = True
    priority: Priority = Priority.MEDIUM
    custom_interval: Optional[int] = None  # minutes
    tags: List[str] = None

class AlarmLogger:
    def __init__(self, log_dir: Path) -> None:
        self.log_dir = log_dir
        self.log_dir.mkdir(exist_ok=True)
        logging.basicConfig(
            filename=self.log_dir / "alarm.log",
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def log_event(self, event_type: str, message: str) -> None:
        logging.info(f"{event_type}: {message}")

class DataManager:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        self.alarm_file = self.data_dir / "alarms.json"
        self.schedule_file = self.data_dir / "schedules.json"
        self.backup_dir = self.data_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.alarm_file.exists():
            backup_file = self.backup_dir / f"alarms_{timestamp}.json"
            backup_file.write_bytes(self.alarm_file.read_bytes())
        if self.schedule_file.exists():
            backup_file = self.backup_dir / f"schedules_{timestamp}.json"
            backup_file.write_bytes(self.schedule_file.read_bytes())

    def load_alarms(self) -> List[AlarmData]:
        if not self.alarm_file.exists():
            return []
        try:
            with open(self.alarm_file, "r") as f:
                data = json.load(f)
                return [
                    AlarmData(
                        time=datetime.fromisoformat(item["time"]),
                        message=item["message"],
                        enabled=item["enabled"],
                        priority=Priority(item.get("priority", "medium")),
                        snooze_count=item.get("snooze_count", 0),
                        max_snooze=item.get("max_snooze", 3),
                        snooze_interval=item.get("snooze_interval", 5),
                        tags=item.get("tags", [])
                    ) for item in data
                ]
        except json.JSONDecodeError:
            return []

    def save_alarms(self, alarms: List[AlarmData]) -> None:
        self.create_backup()
        with open(self.alarm_file, "w") as f:
            json.dump([
                {
                    "time": alarm.time.isoformat(),
                    "message": alarm.message,
                    "enabled": alarm.enabled,
                    "priority": alarm.priority.value,
                    "snooze_count": alarm.snooze_count,
                    "max_snooze": alarm.max_snooze,
                    "snooze_interval": alarm.snooze_interval,
                    "tags": alarm.tags or []
                } for alarm in alarms
            ], f, indent=2)

    def load_schedules(self) -> Dict[str, ScheduleData]:
        if not self.schedule_file.exists():
            return {}
        try:
            with open(self.schedule_file, "r") as f:
                data = json.load(f)
                return {
                    name: ScheduleData(
                        time=datetime.strptime(item["time"], "%H:%M").time(),
                        message=item["message"],
                        repeat=RepeatType(item["repeat"]),
                        enabled=item["enabled"],
                        priority=Priority(item.get("priority", "medium")),
                        custom_interval=item.get("custom_interval"),
                        tags=item.get("tags", [])
                    ) for name, item in data.items()
                }
        except json.JSONDecodeError:
            return {}

    def save_schedules(self, schedules: Dict[str, ScheduleData]) -> None:
        self.create_backup()
        with open(self.schedule_file, "w") as f:
            json.dump({
                name: {
                    "time": schedule.time.strftime("%H:%M"),
                    "message": schedule.message,
                    "repeat": schedule.repeat.value,
                    "enabled": schedule.enabled,
                    "priority": schedule.priority.value,
                    "custom_interval": schedule.custom_interval,
                    "tags": schedule.tags or []
                } for name, schedule in schedules.items()
            }, f, indent=2)

class NotificationManager:
    def __init__(self) -> None:
        self.tts = Voicepods()
        self._lock = Lock()
        self.callbacks: Dict[Priority, List[Callable]] = {
            priority: [] for priority in Priority
        }

    def register_callback(self, priority: Priority, callback: Callable) -> None:
        self.callbacks[priority].append(callback)

    def notify(self, message: str, priority: Priority = Priority.MEDIUM) -> None:
        with self._lock:
            try:
                audio_file = self.tts.tts(message)
                self.tts.play_audio(audio_file)
                
                # Execute priority-based callbacks
                for callback in self.callbacks[priority]:
                    try:
                        callback(message, priority)
                    except Exception as e:
                        logging.error(f"Callback error: {e}")
            except Exception as e:
                logging.error(f"Notification error: {e}")

class AlarmManager:
    def __init__(self, data_dir: Union[str, Path] = Path("DATA")) -> None:
        self.data_dir = Path(data_dir)
        self.data_manager = DataManager(self.data_dir)
        self.logger = AlarmLogger(self.data_dir / "logs")
        self.notification_manager = NotificationManager()
        self.alarms: List[AlarmData] = self.data_manager.load_alarms()
        self.schedules: Dict[str, ScheduleData] = self.data_manager.load_schedules()
        self._running = False
        self._thread: Optional[Thread] = None
        self._lock = Lock()
        self._stop_event = Event()

    def add_alarm(self, time_str: str, message: str, priority: Priority = Priority.MEDIUM,
                 max_snooze: int = 3, snooze_interval: int = 5, tags: List[str] = None) -> None:
        with self._lock:
            alarm_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            alarm = AlarmData(
                time=alarm_time,
                message=message,
                priority=priority,
                max_snooze=max_snooze,
                snooze_interval=snooze_interval,
                tags=tags or []
            )
            self.alarms.append(alarm)
            self.alarms.sort(key=lambda x: x.time)
            self.data_manager.save_alarms(self.alarms)
            self.logger.log_event("ALARM_ADDED", f"New alarm set for {time_str}")

    def snooze_alarm(self, alarm: AlarmData) -> bool:
        if alarm.snooze_count >= alarm.max_snooze:
            return False
        
        alarm.snooze_count += 1
        alarm.time = datetime.now() + timedelta(minutes=alarm.snooze_interval)
        self.data_manager.save_alarms(self.alarms)
        self.logger.log_event("ALARM_SNOOZED", 
                            f"Alarm snoozed for {alarm.snooze_interval} minutes")
        return True

    def add_schedule(self, name: str, time_str: str, message: str,
                    repeat: RepeatType = RepeatType.DAILY,
                    priority: Priority = Priority.MEDIUM,
                    custom_interval: Optional[int] = None,
                    tags: List[str] = None) -> None:
        with self._lock:
            schedule_time = datetime.strptime(time_str, "%H:%M").time()
            schedule_data = ScheduleData(
                time=schedule_time,
                message=message,
                repeat=repeat,
                priority=priority,
                custom_interval=custom_interval,
                tags=tags or []
            )
            
            self.schedules[name] = schedule_data
            self._setup_schedule(name, schedule_data)
            self.data_manager.save_schedules(self.schedules)
            self.logger.log_event("SCHEDULE_ADDED", 
                                f"New schedule '{name}' added for {time_str}")

    def _setup_schedule(self, name: str, schedule_data: ScheduleData) -> None:
        schedule.clear(name)
        if not schedule_data.enabled:
            return

        time_str = schedule_data.time.strftime("%H:%M")
        job = schedule.every()
        
        if schedule_data.repeat == RepeatType.CUSTOM and schedule_data.custom_interval:
            job.minutes.do(self._trigger_schedule, name, schedule_data.message)
        elif schedule_data.repeat == RepeatType.DAILY:
            job.day.at(time_str)
        elif schedule_data.repeat == RepeatType.WEEKLY:
            job.week.at(time_str)
        elif schedule_data.repeat == RepeatType.MONTHLY:
            job.month.at(time_str)
        elif schedule_data.repeat == RepeatType.YEARLY:
            if datetime.now().strftime("%H:%M") == time_str:
                self._trigger_schedule(name, schedule_data.message)
        
        if schedule_data.repeat != RepeatType.CUSTOM:
            job.do(self._trigger_schedule, name, schedule_data.message).tag(name)

    def get_alarms_by_tag(self, tag: str) -> List[AlarmData]:
        return [alarm for alarm in self.alarms if tag in (alarm.tags or [])]

    def get_schedules_by_tag(self, tag: str) -> Dict[str, ScheduleData]:
        return {name: schedule for name, schedule in self.schedules.items() 
                if tag in (schedule.tags or [])}

    def _trigger_schedule(self, name: str, message: str) -> None:
        schedule_data = self.schedules.get(name)
        if schedule_data and schedule_data.enabled:
            self.notification_manager.notify(message, schedule_data.priority)
            self.logger.log_event("SCHEDULE_TRIGGERED", 
                                f"Schedule '{name}' triggered: {message}")

    def _check_alarms(self) -> None:
        now = datetime.now()
        with self._lock:
            triggered = [alarm for alarm in self.alarms 
                        if alarm.enabled and alarm.time <= now]
            for alarm in triggered:
                self.notification_manager.notify(alarm.message, alarm.priority)
                self.logger.log_event("ALARM_TRIGGERED", 
                                    f"Alarm triggered: {alarm.message}")
                self.alarms.remove(alarm)
            if triggered:
                self.data_manager.save_alarms(self.alarms)

    def _run(self) -> None:
        while not self._stop_event.is_set() and self._running:
            schedule.run_pending()
            self._check_alarms()
            time_module.sleep(1)

    def start(self) -> None:
        if not self._thread or not self._thread.is_alive():
            self._running = True
            self._stop_event.clear()
            self._thread = Thread(target=self._run, daemon=True)
            self._thread.start()
            self.logger.log_event("SYSTEM", "Alarm Manager started")

    def stop(self) -> None:
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        self.logger.log_event("SYSTEM", "Alarm Manager stopped")

if __name__ == "__main__":
    alarm_manager = AlarmManager()
    
    # Example usage with new features
    alarm_manager.add_alarm(
        "2024-09-09 12:20:00",
        "Time for meeting!",
        priority=Priority.HIGH,
        tags=["work", "meeting"]
    )
    
    alarm_manager.add_schedule(
        "Daily Break",
        "12:25",
        "Take a break!",
        repeat=RepeatType.DAILY,
        priority=Priority.MEDIUM,
        tags=["health", "routine"]
    )
    
    # Custom interval schedule (every 30 minutes)
    alarm_manager.add_schedule(
        "Water Reminder",
        "00:00",
        "Drink water!",
        repeat=RepeatType.CUSTOM,
        custom_interval=30,
        tags=["health"]
    )
    
    # Add a notification callback for critical priorities
    def critical_callback(message: str, priority: Priority) -> None:
        if priority == Priority.CRITICAL:
            # Additional handling for critical notifications
            print(f"CRITICAL ALERT: {message}")
    
    alarm_manager.notification_manager.register_callback(
        Priority.CRITICAL,
        critical_callback
    )
    
    alarm_manager.start()
    
    try:
        while True:
            time_module.sleep(1)
    except KeyboardInterrupt:
        alarm_manager.stop()