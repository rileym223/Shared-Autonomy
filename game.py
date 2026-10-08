import pygame
import math
import sys
import os
import argparse
import csv
import json
import time
import uuid
from datetime import datetime, timezone
from pygamepopup.menu_manager import MenuManager
from pygamepopup.components import Button, InfoBox
import pygamepopup


"""
TODO:
find a them for this game, and find assests, could make it into space theme or just organizing the household objects. food items I already have.
- I found UI asset pack https://www.kenney.nl/assets/ui-pack-sci-fi
Make an agent class, that handles things based on current states of the game. (research into that will be needed)
 - 4 different types of agents (no ask, ask yes and no, ask which option, ask)
 - Proacive and reactive in these different agents
 - Click C to call the agent, asks which task to be done, or asks should i do this yes or no
  - agent does not ask
  - agent asks on its own
make a button class that is reusable to create something that i can use quite often
choose a real game flow, point and drag items acrross the screen, I feel like the task is not going to be very engaging that needs to be discussed more
could go into cleaning the house game/organizer all the different items.
"""

"""
BY EOD:
 set up the task, totally
  - table png //done
  - fork png //done 
  - knife png //done 
  - spoon png //done 
  - placemat //done 
  - cup png //done 
  - napkin png //done 
  - create a place where they are all supposed to go, do not give user access to all of the items, give the agent some of the items that block other items from the user
  contunuing the task 

  Task FLow: 
    Placemat needs to go before the plate, fork, knife, spoon and napkin
    napkin needs to go before fork, spoon and knife go to the left of the plate, on top of placemat.

  TODO:
    - Get the buttons nice and make the task flow an actual thing.
    - bug found when the user brings up the call menu, the player gets soft locked into clicking on an item and cannot escpae for now'

"""


pygame.init()
pygamepopup.init()

pygamepopup.configuration.set_info_box_background("Default/button_square_header_small_rectangle_screws.png")


# Ordered floor path tuned to the kitchen background.
# Edit these points to match walkable floor in bigfloorv3.png.
FLOOR_WAYPOINTS = [
    (367, 110),
     (452, 105),
     (539, 97),
     (691, 97),
     (844, 99),
     (1001, 108),
     (1007, 211),
     (1007, 308),
     (870, 300),
     (742, 305),
     (570, 291),
     (412, 298),
     (406, 400),
     (416, 476),
     (531, 478),
     (658, 506),
     (744, 564),
     (811, 639),
]

LAYOUTS = {
    "1": {
        "positions": {
            "Plate": (650, 383), "Spoon": (137, 7), "Fork": (33, 112),
            "Person": (300, 70), "Salt": (447, 19), "Knife": (505, 16),
            "Cup": (211, 11), "Napkin": (812, 11), "Placemat": (750, 370),
        },
        "held_items": ("Napkin", "Placemat", "Plate"),
        "menu_start_y": 650,
        "menu_rows": 3,
    },
    "2": {
        "positions": {
            "Plate": (11, 90), "Spoon": (692, 396), "Fork": (715, 396),
            "Person": (300, 100), "Salt": (1053, 20), "Knife": (1154, 96),
            "Cup": (812, 12), "Napkin": (137, 7), "Placemat": (91, 557),
        },
        "held_items": ("Fork", "Knife", "Cup", "Salt", "Spoon"),
        "menu_start_y": 650,
        "menu_rows": 3,
    },
    "3": {
        "positions": {
            "Plate": (830, 388), "Spoon": (692, 396), "Fork": (715, 396),
            "Person": (300, 100), "Salt": (1053, 20), "Knife": (1154, 96),
            "Cup": (812, 12), "Napkin": (1135, 22), "Placemat": (693, 180),
        },
        "held_items": ("Fork", "Knife", "Cup", "Napkin", "Spoon", "Placemat", "Salt", "Plate"),
        "menu_start_y": 600,
        "menu_rows": 4,
    },
    "4": {
        "positions": {
            "Plate": (521, 391), "Spoon": (137, 7), "Fork": (33, 112),
            "Person": (300, 150), "Salt": (447, 19), "Knife": (505, 16),
            "Cup": (211, 11), "Napkin": (321, 10), "Placemat": (107, 570),
        },
        "held_items": ("Napkin", "Placemat", "Plate"),
        "menu_start_y": 650,
        "menu_rows": 3,
    },
}


def get_active_layout():
    if __name__ != "__main__":
        return LAYOUTS["1"]

    parser = argparse.ArgumentParser(description="Run the table-setting game.")
    parser.add_argument("--layout", choices=LAYOUTS, help="starting object layout (1-4)")
    for layout_id in LAYOUTS:
        parser.add_argument(f"-{layout_id}", dest="legacy_layout", action="store_const", const=layout_id)
    arguments = parser.parse_args()
    return LAYOUTS[arguments.layout or arguments.legacy_layout or "1"]


ACTIVE_LAYOUT = get_active_layout()
ACTIVE_LAYOUT_ID = next(
    layout_id for layout_id, layout in LAYOUTS.items() if layout is ACTIVE_LAYOUT
)

DATA_DIR = "study_data"
IDLE_THRESHOLD_SECONDS = 3.0
DEBUG_METRICS = False

ITEM_PREREQUISITES = {
    "Placemat": (),
    "Plate": ("Placemat",),
    "Fork": ("Placemat", "Napkin"),
    "Knife": ("Placemat", "Napkin"),
    "Spoon": ("Placemat", "Napkin"),
    "Napkin": ("Placemat",),
    "Cup": ("Placemat", "Plate"),
    "Salt": ("Placemat",),
}


def get_unsatisfied_prerequisites(item, sprite_group):
    sprites_by_name = {sprite.name: sprite for sprite in sprite_group}
    return [
        prerequisite
        for prerequisite in ITEM_PREREQUISITES.get(item.name, ("Placemat",))
        if prerequisite not in sprites_by_name or not sprites_by_name[prerequisite].snapped
    ]


def check_task_complete(items_by_name):
    return all(items_by_name[name].snapped for name in ITEM_PREREQUISITES)


class GameMetrics:
    """Collect behavioral study data without owning game behavior."""

    def __init__(self, layout_id, data_dir=DATA_DIR):
        self.launch_time = time.perf_counter()
        self.start_time = datetime.now(timezone.utc).isoformat()
        self.session_id = str(uuid.uuid4())
        self.layout_id = str(layout_id)
        self.data_dir = data_dir
        self.first_action_time = None
        self.last_meaningful_player_action_time = None
        self.stop_time = None
        self.finalized = False
        self.task_completed = False
        self.save_error = None
        self._last_update_time = self.launch_time
        self._is_player_moving = False
        self._activity_since_update = False
        self._idle_episode_start = None
        self._robot_phase = "idle"
        self._robot_phase_started_at = self.launch_time
        self._post_robot_windows = []

        self.summary_counts = {
            "total_placement_attempts": 0,
            "total_successful_placements": 0,
            "total_failed_placements": 0,
            "total_dependency_errors": 0,
            "total_cancellations": 0,
            "robot_call_count": 0,
            "robot_deliveries": 0,
        }
        self.idle_totals = {
            "total_inactivity_time": 0.0,
            "total_thresholded_idle_time": 0.0,
        }
        self.robot_totals = {
            "total_active_time": 0.0,
            "robot_wait_time": 0.0,
        }
        self.items = {
            item_name: {
                "number_of_failed_attempts": 0,
                "number_of_dependency_blocks": 0,
                "successful": False,
            }
            for item_name in ITEM_PREREQUISITES
        }

        self._debug_metric("SESSION_START", self.launch_time)

    def _debug_metric(self, metric_name, now=None, item_name=None, **details):
        if DEBUG_METRICS:
            label = f": {item_name}" if item_name else ""
            if metric_name == "IDLE_END":
                print(f"[METRICS] Idle end: {details.get('duration', 0.0):.2f}s")
            else:
                print(f"[METRICS] {metric_name.replace('_', ' ').title()}{label}")

    def _finish_idle_episode(self, now):
        if self._idle_episode_start is None:
            return
        duration = max(0.0, now - self._idle_episode_start)
        self.idle_totals["total_thresholded_idle_time"] += duration
        self._debug_metric("IDLE_END", now, duration=duration)
        self._idle_episode_start = None

    def _mark_activity(self, event_type, item_name=None, now=None, log_event=True):
        if self.finalized:
            return
        now = time.perf_counter() if now is None else now
        if self.first_action_time is None:
            self.first_action_time = now
            self._debug_metric("TASK_FIRST_ACTION", now, action=event_type)
        elif self.last_meaningful_player_action_time is not None:
            gap = max(0.0, now - self.last_meaningful_player_action_time)
            self.idle_totals["total_inactivity_time"] += gap
            self._finish_idle_episode(now)

        self.last_meaningful_player_action_time = now
        self._activity_since_update = True
        for window in self._post_robot_windows:
            if window["latency"] is None and now >= window["completed_at"]:
                window["latency"] = now - window["completed_at"]
        if log_event:
            self._debug_metric(event_type, now, item_name=item_name)

    def record_item_interaction(self, item, now=None):
        now = time.perf_counter() if now is None else now
        self._mark_activity("ITEM_INTERACTION", item.name, now)

    def record_robot_zone_attempt(self, item, position, now=None):
        now = time.perf_counter() if now is None else now
        self._mark_activity("ROBOT_ZONE_ACCESS_ATTEMPT", item.name, now, log_event=False)
        self._debug_metric(
            "ROBOT_ZONE_ACCESS_ATTEMPT", now, item.name,
            position=[int(position[0]), int(position[1])],
        )

    def record_pickup(self, item, now=None):
        now = time.perf_counter() if now is None else now
        self._mark_activity("ITEM_PICKUP", item.name, now)

    def record_placement_attempt(self, item, actor, unsatisfied_prerequisites=(), now=None):
        now = time.perf_counter() if now is None else now
        item_data = self.items[item.name]
        self._mark_activity("PLACEMENT_ATTEMPT", item.name, now, log_event=False)
        self.summary_counts["total_placement_attempts"] += 1
        if unsatisfied_prerequisites and actor == "human":
            item_data["number_of_dependency_blocks"] += 1
            self.summary_counts["total_dependency_errors"] += 1
            self._debug_metric(
                "DEPENDENCY_BLOCK", now, item.name,
                unsatisfied_prerequisites=list(unsatisfied_prerequisites),
            )
        self._debug_metric("PLACEMENT_ATTEMPT", now, item.name, actor=actor)

    def record_placement_failure(self, item, actor, unsatisfied_prerequisites=(), now=None):
        now = time.perf_counter() if now is None else now
        item_data = self.items[item.name]
        item_data["number_of_failed_attempts"] += 1
        self.summary_counts["total_failed_placements"] += 1
        self._debug_metric(
            "PLACEMENT_FAILED", now, item.name,
            actor=actor,
            unsatisfied_prerequisites=list(unsatisfied_prerequisites),
        )

    def record_placement_success(self, item, actor, now=None):
        now = time.perf_counter() if now is None else now
        item_data = self.items[item.name]
        if item_data["successful"]:
            return
        item_data["successful"] = True
        self.summary_counts["total_successful_placements"] += 1
        self._debug_metric("PLACEMENT_SUCCESS", now, item.name, actor=actor)
        if actor == "robot":
            self.summary_counts["robot_deliveries"] += 1
            self._post_robot_windows.append({
                "completed_at": now,
                "latency": None,
            })
            self._debug_metric("ROBOT_DELIVERY_COMPLETE", now, item.name)

    def record_cancellation(self, item=None, source="item", now=None):
        now = time.perf_counter() if now is None else now
        item_name = item.name if item is not None else None
        self._mark_activity("CANCELLATION", item_name, now, log_event=False)
        self.summary_counts["total_cancellations"] += 1
        self._debug_metric("CANCELLATION", now, item_name, source=source)

    def record_robot_call(self, now=None):
        now = time.perf_counter() if now is None else now
        self._mark_activity("ROBOT_CALL", now=now, log_event=False)
        self.summary_counts["robot_call_count"] += 1
        self._debug_metric("ROBOT_CALL", now)

    def record_robot_selection(self, item, now=None):
        now = time.perf_counter() if now is None else now
        self._debug_metric("ROBOT_ITEM_SELECTION", now, item.name, actor="robot")
        self.record_placement_attempt(item, "robot", now=now)

    def record_robot_phase(self, phase, now=None):
        now = time.perf_counter() if now is None else now
        if phase == self._robot_phase:
            return
        self._close_robot_phase(now)
        self._robot_phase = phase
        self._robot_phase_started_at = now
        self._debug_metric("ROBOT_PHASE_START", now, phase=phase)

    def _close_robot_phase(self, now):
        if self._robot_phase == "idle":
            return
        duration = max(0.0, now - self._robot_phase_started_at)
        self.robot_totals["total_active_time"] += duration

    def record_frame(self, now=None, player_moving=False):
        if self.finalized:
            return
        now = time.perf_counter() if now is None else now
        frame_duration = max(0.0, now - self._last_update_time)
        if player_moving:
            if not self._is_player_moving:
                self._mark_activity("PLAYER_MOVEMENT_START", now=now)
            else:
                self.last_meaningful_player_action_time = now
                self._activity_since_update = True
            self._is_player_moving = True
        else:
            self._is_player_moving = False

        if self._robot_phase != "idle" and not self._activity_since_update:
            self.robot_totals["robot_wait_time"] += frame_duration
        self._update_idle(now)
        self._activity_since_update = False
        self._last_update_time = now

    def _update_idle(self, now):
        last_action = self.last_meaningful_player_action_time
        if last_action is None:
            return
        inactivity_duration = max(0.0, now - last_action)
        if inactivity_duration > IDLE_THRESHOLD_SECONDS and self._idle_episode_start is None:
            self._idle_episode_start = last_action + IDLE_THRESHOLD_SECONDS
            self._debug_metric("IDLE_START", self._idle_episode_start)

    def record_drag_motion(self, now=None):
        if self.finalized:
            return
        now = time.perf_counter() if now is None else now
        self._mark_activity("ITEM_DRAG_MOTION", now=now, log_event=False)

    def finalize(self, completed=False, now=None):
        if self.finalized:
            return
        now = time.perf_counter() if now is None else now
        self.task_completed = bool(completed)
        if self.task_completed:
            self._debug_metric("TASK_COMPLETE", now)
        else:
            self._debug_metric("SESSION_END", now, reason="window_closed")
        if self.last_meaningful_player_action_time is not None:
            gap = max(0.0, now - self.last_meaningful_player_action_time)
            self.idle_totals["total_inactivity_time"] += gap
            self._finish_idle_episode(now)
        self._close_robot_phase(now)
        self.stop_time = now
        self.finalized = True
        self._save()

    def _summary(self):
        end = self.stop_time if self.stop_time is not None else time.perf_counter()
        total_task_time = max(0.0, end - self.launch_time)
        time_to_first_action = (
            max(0.0, self.first_action_time - self.launch_time)
            if self.first_action_time is not None else None
        )
        active_task_time = 0.0
        if self.first_action_time is not None:
            active_task_time = max(
                0.0,
                end - self.first_action_time - self.idle_totals["total_inactivity_time"],
            )
        placement_accuracy = (
            self.summary_counts["total_successful_placements"]
            / self.summary_counts["total_placement_attempts"]
            if self.summary_counts["total_placement_attempts"] else None
        )
        post_latencies = [
            window["latency"]
            for window in self._post_robot_windows
            if window["latency"] is not None
        ]
        return {
            "session_id": self.session_id,
            "layout_id": self.layout_id,
            "start_time": self.start_time,
            "task_completed": self.task_completed,
            "total_task_time": total_task_time,
            "active_task_time": active_task_time,
            "time_to_first_action": time_to_first_action,
            "total_placement_attempts": self.summary_counts["total_placement_attempts"],
            "total_successful_placements": self.summary_counts["total_successful_placements"],
            "total_failed_placements": self.summary_counts["total_failed_placements"],
            "placement_accuracy": placement_accuracy,
            "total_dependency_blocks": self.summary_counts["total_dependency_errors"],
            "dependency_blocks_per_item": {
                name: data["number_of_dependency_blocks"] for name, data in self.items.items()
            },
            "total_cancellations": self.summary_counts["total_cancellations"],
            "thresholded_idle_time": self.idle_totals["total_thresholded_idle_time"],
            "robot_call_count": self.summary_counts["robot_call_count"],
            "robot_deliveries": self.summary_counts["robot_deliveries"],
            "robot_wait_time": self.robot_totals["robot_wait_time"],
            "total_robot_active_time": self.robot_totals["total_active_time"],
            "post_robot_engagement_latency_mean": self._mean(post_latencies),
        }

    @staticmethod
    def _mean(values):
        observed = [value for value in values if value is not None]
        return sum(observed) / len(observed) if observed else None

    def _save(self):
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            summary = self._summary()
            items = {
                name: {
                    "number_of_failed_attempts": data["number_of_failed_attempts"],
                    "number_of_dependency_blocks": data["number_of_dependency_blocks"],
                }
                for name, data in self.items.items()
            }
            result = {"summary": summary}
            json_path = os.path.join(
                self.data_dir,
                f"study_session_{self.session_id}_layout{self.layout_id}.json",
            )
            with open(json_path, "w", encoding="utf-8") as output:
                json.dump(result, output, indent=2)
                output.flush()
            self._append_csv(
                os.path.join(self.data_dir, "study_summary.csv"),
                summary,
            )
            item_rows = []
            for item_name, item_data in items.items():
                item_rows.append({
                    "session_id": self.session_id,
                    "layout_id": self.layout_id,
                    "item_name": item_name,
                    **item_data,
                })
            self._append_csv(os.path.join(self.data_dir, "study_items.csv"), item_rows)
        except Exception as error:
            self.save_error = str(error)

    @staticmethod
    def _append_csv(path, rows):
        if not isinstance(rows, list):
            rows = [rows]
        if not rows:
            return
        fields = list(dict.fromkeys(key for row in rows for key in row))
        write_header = not os.path.exists(path) or os.path.getsize(path) == 0
        if not write_header:
            with open(path, "r", newline="", encoding="utf-8-sig") as existing:
                reader = csv.DictReader(existing)
                existing_fields = reader.fieldnames or []
                existing_rows = list(reader)
            if (
                os.path.basename(path) in {"study_summary.csv", "study_items.csv"}
                and existing_fields != fields
            ):
                with open(path, "w", newline="", encoding="utf-8-sig") as output:
                    writer = csv.DictWriter(output, fieldnames=fields)
                    writer.writeheader()
                    for row in existing_rows:
                        writer.writerow({key: row.get(key, "") for key in fields})
            elif existing_fields:
                fields = existing_fields
        with open(path, "a", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
            if write_header:
                writer.writeheader()
            for row in rows:
                writer.writerow({
                    key: json.dumps(value)
                    if isinstance(value, (dict, list, tuple)) else value
                    for key, value in row.items()
                })
            output.flush()

 

# (310, 490),
# (809, 335),
# (1014, 327),
# (1029, 229),
# (1019, 132),
# (925, 135),
# (784, 132),
# (688, 134),
# (614, 130),
# (513, 134), 
# (452, 133),
# (438, 210),
# (438, 255)
# (373, 299),
# (303, 359),
# (310, 418),
# (364, 475),
# (484, 498),
# (635, 517),
# (698, 535),
# (703, 594),
# (703, 656),
# (710, 689),
# (766, 707),

# (779, 478),
# (553, 488),
# (407, 475),
# (384, 293),
# (381, 105),
# (570, 82),
# (662, 97),
# (848, 110),
# (947, 109),
# (1004, 111),
# (1012, 226),
# (995, 288),
# (764, 317),
# (599, 302),
# (342, 323),
# (278, 400),
# (191, 464),
# (850, 672),



class ResponiveAgent:
    """Reactive, 'ask which option' agent.

    Holds a set of items in the robot-only zone that the player cannot
    drag out directly. Pressing C opens a menu listing those items; picking
    one makes the robot drive along FLOOR_WAYPOINTS to the item, grab it,
    then follow waypoints to the goal location.
    """
    
    PHASE_IDLE = "idle"
    PHASE_TO_ITEM = "to_item"
    PHASE_TO_GOAL = "to_goal"
    PHASE_RETURN_HOME = "return_home"

    def __init__(
        self, held_items, menu_manager, robot,
        waypoints=None, speed=350, menu_start_y=650, menu_rows=3, metrics=None,
    ):
        self.held_items = list(held_items)   # Sprites currently blocked in robot space
        self.menu_manager = menu_manager
        self.speed = speed
        self.menu_start_y = menu_start_y
        self.menu_rows = menu_rows
        self.metrics = metrics
        self.robot = robot
        self.start_location = pygame.Vector2(self.robot.rect.topleft)
        self.waypoints = [pygame.Vector2(p) for p in (waypoints or FLOOR_WAYPOINTS)]

        self.choice_box = None
        self.choice_buttons = []
        self.active_item = None  # item currently being delivered
        self.is_delivering = False
        self.phase = self.PHASE_IDLE
        self.carry_offset = pygame.Vector2(0, 0)
        self.path_queue = []                 # Vector2 targets to visit in order

    def call(self):
        """Show custom selection buttons in the bottom-right blue area."""
        if self.is_delivering or not self.held_items:
            return

        self.choice_buttons = []
        start_x = 700
        start_y = self.menu_start_y
        button_w = 220
        button_h = 46
        gap = 54

        for index, item in enumerate(self.held_items):
            column, row = divmod(index, self.menu_rows)
            button = myButton(
                title=item.name,
                x=start_x + column * (button_w + 40),
                y=start_y + row * gap,
                width=button_w,
                height=button_h,
                callback=self._make_selector(item),
                font=font,
                image_path="Default/button_square_header_small_rectangle_screws.png",
            )
            self.choice_buttons.append(button)

        self.choice_box = True
        if self.metrics:
            self.metrics.record_robot_call()

    def _make_selector(self, item):
        # each button needs its own callback bound to its own item
        return lambda: self.select_item(item)

    def select_item(self, item):
        if item not in self.held_items:
            return
        if self.metrics:
            self.metrics.record_robot_selection(item)
        self.held_items.remove(item)
        self.active_item = item
        self.is_delivering = True
        self.phase = self.PHASE_TO_ITEM
        if self.metrics:
            self.metrics.record_robot_phase(self.phase)
        self.path_queue = self._build_path(item.rect.topleft)
        self.choice_buttons = []
        self.choice_box = None

    def draw_choice_buttons(self, surface):
        for button in self.choice_buttons:
            button.draw(surface)

    def cancel_choice(self):
        if self.choice_buttons and self.metrics:
            self.metrics.record_cancellation(source="robot_menu")
        self.choice_buttons = []
        self.choice_box = None

    def _nearest_waypoint_index(self, pos):
        return min(
            range(len(self.waypoints)),
            key=lambda i: (self.waypoints[i] - pos).length_squared(),
        )

    def _build_path(self, destination):
        """Build a queue: along waypoints from robot toward destination, then destination."""
        start = pygame.Vector2(self.robot.rect.topleft)
        dest = pygame.Vector2(destination)

        if not self.waypoints:
            return [dest]

        i_start = self._nearest_waypoint_index(start)
        i_end = self._nearest_waypoint_index(dest)

        if i_start <= i_end:
            route = self.waypoints[i_start : i_end + 1]
        else:
            route = list(reversed(self.waypoints[i_end : i_start + 1]))

        path = []
        for wp in route:
            if (wp - start).length() > 12:
                path.append(pygame.Vector2(wp))

        if not path or (path[-1] - dest).length() > 4:
            path.append(dest)
        else:
            path[-1] = dest

        return path

    def _move_robot_toward(self, target, dt):
        """Move the robot toward target. Returns remaining distance."""
        current = pygame.Vector2(self.robot.rect.topleft)
        direction = target - current
        dist = direction.length()
        if dist < 4:
            self.robot.rect.topleft = target
            return 0

        step = direction.normalize() * min(self.speed * dt, dist)
        self.robot.rect.topleft = current + step
        return (target - pygame.Vector2(self.robot.rect.topleft)).length()

    def _follow_path(self, dt):
        """Advance along path_queue. Returns True when the final point is reached."""
        if not self.path_queue:
            return True

        remaining = self._move_robot_toward(self.path_queue[0], dt)
        if remaining < 4:
            self.path_queue.pop(0)
            if not self.path_queue:
                return True
        return False

    def update(self, dt):
        if not self.is_delivering:
            return

        if self.phase == self.PHASE_TO_ITEM:
            if self.active_item is None:
                return
            if self._follow_path(dt):
                # Grab: keep the item's offset relative to the robot so it rides along
                self.carry_offset = (
                    pygame.Vector2(self.active_item.rect.topleft)
                    - pygame.Vector2(self.robot.rect.topleft)
                )
                self.phase = self.PHASE_TO_GOAL
                if self.metrics:
                    self.metrics.record_robot_phase(self.phase)
                robot_destination = (
                    pygame.Vector2(self.active_item.goal) - self.carry_offset
                )
                self.path_queue = self._build_path(robot_destination)

        elif self.phase == self.PHASE_TO_GOAL:
            if self.active_item is None:
                return
            done = self._follow_path(dt)
            self.active_item.rect.topleft = (
                pygame.Vector2(self.robot.rect.topleft) + self.carry_offset
            )
            if done:
                self.active_item.rect.topleft = self.active_item.goal
                self.active_item.snapped = True
                if self.metrics:
                    self.metrics.record_placement_success(self.active_item, "robot")
                self.active_item = None
                self.phase = self.PHASE_RETURN_HOME
                if self.metrics:
                    self.metrics.record_robot_phase(self.phase)
                self.path_queue = self._build_path(self.start_location)

        elif self.phase == self.PHASE_RETURN_HOME:
            done = self._follow_path(dt)
            if done:
                self.is_delivering = False
                self.phase = self.PHASE_IDLE
                if self.metrics:
                    self.metrics.record_robot_phase(self.phase)
                self.path_queue = []

    @property
    def is_menu_open(self):
        return bool(self.choice_buttons)


class Sprite(pygame.sprite.Sprite):
    def __init__(self, goal: pygame.Vector2, height, width, asset, name=None):
        super().__init__()

        self.popup = InfoBox(
            "Item not dropped in the correct sequence action blocked (error)",
            [[]],
            element_linked = pygame.Rect(0,0,600,600),
            position=(0, 200),
            width=600,
            has_close_button=True,
            background_path="Default/bar_round_large.png"
        )

        self.popup2 = InfoBox(
                    "Item Placement canceled ",
                    [[]],
                    element_linked = pygame.Rect(0,0,600,600),
                    position=(0, 200),
                    width=600,
                    has_close_button=True,
                    background_path="Default/bar_round_large.png"
                )

        self.snapped = False
        self.snap_radius =15
        self.goal = goal
        self.height = height
        self.width = width
        self.image = pygame.image.load(os.path.join("assests", asset)).convert_alpha()
        self.image = pygame.transform.scale(self.image, (height, width))
        self.rect = self.image.get_rect()
        self.dragging = False
        self.drag_offset = pygame.Vector2(0, 0)
        self.name = name or asset
        self.original_position = pygame.Vector2(self.rect.topleft)
        self.metrics = None

    def show_box(self):
        return self.popup

    def show_box2(self):
        return self.popup2

    def remember_position(self):
        """Save the sprite's current position as its spawn position."""
        self.original_position = pygame.Vector2(self.rect.topleft)

    def send_to_spawn(self):
        self.rect.topleft = self.original_position

    def start_drag(self, mouse_pos: tuple[int, int]) -> None:
        if self.name == "Robot" or self.snapped:
            self.dragging = False
            return
        if mouse_pos[0] >= 600 and mouse_pos[1] <= 600:
            if self.metrics:
                self.metrics.record_robot_zone_attempt(self, mouse_pos)
            self.dragging = False
            return
        if self.metrics:
            self.metrics.record_item_interaction(self)
        self.dragging = False
        self.original_position = pygame.Vector2(self.rect.topleft)
        self.drag_offset = pygame.Vector2(mouse_pos) - pygame.Vector2(self.rect.topleft)


        # If the player begins the drag, check to see if the star drag is true, if it is, draw green
        # sqaure or whatever around the goal location, if it is not draw a red one. 
        
    def get_rect(self) -> tuple:
        return(self.goal[0], self.goal[1], self.height, self.width)

    def stop_drag(self) -> None:
        self.dragging = False

    def drag(self, mouse_pos: tuple[int, int]) -> None:
        if not self.dragging:
            return

        previous_position = self.rect.topleft
        self.rect.topleft = pygame.Vector2(mouse_pos) - self.drag_offset
        if self.rect.topleft != previous_position and self.metrics:
            self.metrics.record_drag_motion()
        if self.check_stop():
            unsatisfied = get_unsatisfied_prerequisites(self, sprite_list)
            allowed = can_place_item(self, sprite_list)
            if self.metrics:
                self.metrics.record_placement_attempt(self, "human", unsatisfied)
            if allowed:
                self.rect.topleft = self.goal
                self.snapped = True
                self.stop_drag()
                if self.metrics:
                    self.metrics.record_placement_success(self, "human")
            else:
                if self.metrics:
                    self.metrics.record_placement_failure(self, "human", unsatisfied)
                self.rect.topleft = self.original_position
                self.stop_drag()
                menu_manager.open_menu(self.popup)

    def check_stop(self) -> bool:
        dist = math.hypot(self.rect.x - self.goal.x, self.rect.y - self.goal.y)
        return dist < self.snap_radius


def can_place_item(item, sprite_group) -> bool:
    """Enforce the placement order for the table-setting task."""
    return not get_unsatisfied_prerequisites(item, sprite_group)

 
screen = pygame.display.set_mode((1200, 840))
PLAYER_BOUNDS = pygame.Rect(0, 0, 1200, 800)

try:
    bg_raw = pygame.image.load("assests/floorpng.png").convert_alpha()
    background = pygame.transform.scale(bg_raw, (1200, 800))
except pygame.error as e:
    print(f"Error loading image: {e}")
    sys.exit()

# Helper functin to draw rect
def draw_alpha_rect(screen, color: pygame.Color, rect):
    surf = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    surf.fill(color)
    screen.blit(surf, (rect[0], rect[1]))


def draw_pickup_area(surface, center, radius):
    """Show the area in which the player can automatically grab an item."""
    area = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
    area_center = pygame.Vector2(radius + 2, radius + 2)
    pygame.draw.circle(area, (55, 190, 220, 32), area_center, radius)
    pygame.draw.circle(area, (120, 230, 245, 210), area_center, radius, width=3)
    surface.blit(area, (center[0] - radius - 2, center[1] - radius - 2))




# Source - https://stackoverflow.com/a/28005796
# Posted by Anthony Pham
# Retrieved 2026-07-02, License - CC BY-SA 3.0

class Background(pygame.sprite.Sprite):
    def __init__(self, image_file, location):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load(image_file)
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = location

class myButton:
    def __init__(self, title, x, y, width, height, callback, font=None, image_path=None):
        self.title = title
        self.rect = pygame.Rect(x, y, width, height)
        self.callback = callback
        self.font = font or pygame.font.SysFont(None, 24)
        self.hovered = False
        self.image = None
        if image_path:
            try:
                self.image = pygame.image.load(image_path).convert_alpha()
                self.image = pygame.transform.scale(self.image, (width, height))
            except pygame.error as e:
                print(f"Could not load button image {image_path}: {e}")

    def draw(self, surface):
        if self.image is not None:
            surface.blit(self.image, self.rect)
        else:
            color = (80, 140, 220) if self.hovered else (60, 110, 190)
            pygame.draw.rect(surface, color, self.rect, border_radius=8)
            pygame.draw.rect(surface, (255, 255, 255), self.rect, width=2, border_radius=8)

        text_surface = self.font.render(self.title, True, (255, 0, 0))
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and self.callback:
                self.callback()
                return True
        return False

# scaled_floor = pygame.transform.scale('assests/floor.png',1200, 850)
# pygame.image.save(scaled_floor, "scaledfloor.png")
BackGround = Background('assests/bigfloorv3.png', [0, 0])



sprite_list = pygame.sprite.LayeredUpdates()

plate = Sprite(pygame.Vector2(357,644), 100, 75, "platepng.png", name="Plate")
plate.rect.topleft = ACTIVE_LAYOUT["positions"]["Plate"]
sprite_list.add(plate)
sprite_list.change_layer(sprite=plate, new_layer=3)


spoon = Sprite(pygame.Vector2(450,654), 60, 60, "spoonpng.png", name="Spoon")
spoon.rect.topleft = ACTIVE_LAYOUT["positions"]["Spoon"]
sprite_list.add(spoon)
sprite_list.change_layer(sprite=spoon, new_layer=3)

# # Fork and knife are held by the agent to start: place them inside the
# # robot-only zone (x >= 600, y <= 600) so start_drag already refuses to
# # let the player pull them out directly.
fork = Sprite(pygame.Vector2(306,651),60, 60, "forkpng.png", name="Fork")
fork.rect.topleft = ACTIVE_LAYOUT["positions"]["Fork"]
sprite_list.add(fork)
sprite_list.change_layer(sprite=fork, new_layer=3)

person = Sprite(pygame.Vector2(306,651),85, 120, "person011.png", name="person")
person.rect.topleft = ACTIVE_LAYOUT["positions"]["Person"]
sprite_list.add(person)
sprite_list.change_layer(sprite=person, new_layer=3)
PLAYER_SPEED = 250
PLAYER_PICKUP_RADIUS = 90

salt = Sprite(pygame.Vector2(389,600),30, 40, "salt.png", name="Salt")
salt.rect.topleft = ACTIVE_LAYOUT["positions"]["Salt"]
sprite_list.add(salt)
sprite_list.change_layer(sprite=salt, new_layer=3)


knife = Sprite(pygame.Vector2(430,654),60, 60, "knifepng.png", name="Knife")
knife.rect.topleft = ACTIVE_LAYOUT["positions"]["Knife"]
sprite_list.add(knife)
sprite_list.change_layer(sprite=knife, new_layer=3)

robot = Sprite(pygame.Vector2(200,248),150, 120, "Armature_Idle_00.png", name="Robot")
robot.rect.x = 975
robot.rect.y = 711
sprite_list.add(robot)
sprite_list.change_layer(sprite=robot, new_layer=0)


cup = Sprite(pygame.Vector2(453, 564), 50, 50, "cuppng.png", name="Cup")
cup.rect.topleft = ACTIVE_LAYOUT["positions"]["Cup"]
sprite_list.add(cup)
sprite_list.change_layer(sprite=cup, new_layer=3)

napkin = Sprite(pygame.Vector2(308,650), 60,65, "napkinpng.png", name="Napkin")
napkin.rect.topleft = ACTIVE_LAYOUT["positions"]["Napkin"]
sprite_list.add(napkin)
sprite_list.change_layer(sprite=napkin, new_layer=2)


placemat = Sprite(pygame.Vector2(303,633),200, 100, "placematpng.png", name="Placemat")
placemat.rect.topleft = ACTIVE_LAYOUT["positions"]["Placemat"]
sprite_list.add(placemat)
sprite_list.change_layer(sprite=placemat, new_layer=1)

for sprite in sprite_list:
    sprite.remember_position()


# table = Sprite(pygame.Vector2(155,198),500, 400, "woodpng.png", name="Table")
# table.rect.x = 100
# table.rect.y = 100
# sprite_list.add(table)
# sprite_list.change_layer(sprite=table, new_layer=0)


pygame.font.match_font(name="Kenney Future Narrow")
font = pygame.font.Font(filename="Kenney Future Narrow.ttf")
textSurfaceObj = font.render('some text', True, (240,240,240), (115,117,117))

menu_manager = MenuManager(screen=screen)


def main():

    dragging_sprite = None
    carried_item = None
    carried_item_offset = pygame.Vector2(0, 0)
    pickup_blocked_item = None

    items_by_name = {
        "Plate": plate,
        "Spoon": spoon,
        "Fork": fork,
        "Salt": salt,
        "Knife": knife,
        "Cup": cup,
        "Napkin": napkin,
        "Placemat": placemat,
    }
    metrics = GameMetrics(ACTIVE_LAYOUT_ID)
    for item in (*items_by_name.values(), robot):
        item.metrics = metrics

    agent = ResponiveAgent(
        held_items=[items_by_name[name] for name in ACTIVE_LAYOUT["held_items"]],
        menu_manager=menu_manager,
        robot=robot,
        menu_start_y=ACTIVE_LAYOUT["menu_start_y"],
        menu_rows=ACTIVE_LAYOUT["menu_rows"],
        metrics=metrics,
    )

    Notibox = InfoBox(
        "Robot Space access only",
        [[]],
        element_linked=pygame.Rect(600, 0, 600, 600),
        position=(600, 200),
        width=600,
        has_close_button=False,
    )



    running = True
    clock = pygame.time.Clock()
    highlight_rect = None
    highlight_color = pygame.Color(0, 220, 0, 50)

    while running:
        dt = clock.tick(60) / 1000  # seconds since last frame, needed for agent movement speed

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                print(f"Mouse clicked at: {event.pos}")
                if agent.is_menu_open:
                    for button in agent.choice_buttons:
                        if button.handle_event(event):
                            break
                    else:
                        menu_manager.click(event.button, event.pos)
                else:
                    clicked_sprite = None
                    for sprite in sprite_list:
                        if sprite in {person, robot} or getattr(sprite, "snapped", False):
                            continue
                        if sprite.rect.collidepoint(event.pos):
                            clicked_sprite = sprite
                            break

                    if clicked_sprite:
                        if clicked_sprite == robot:
                                agent.call()
                        dragging_sprite = clicked_sprite
                        dragging_sprite.start_drag(event.pos)
                    else:
                        menu_manager.click(event.button, event.pos)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if dragging_sprite:
                    was_dragging = dragging_sprite.dragging
                    dragging_sprite.stop_drag()
                    highlight_rect = None
                    highlight_color = pygame.Color(0,0,0,0)
                    print(f"{dragging_sprite.name} final position: ({dragging_sprite.rect.x}, {dragging_sprite.rect.y})")
                    if was_dragging and not dragging_sprite.snapped:
                        carried_item = dragging_sprite
                        metrics.record_pickup(carried_item)
                        carried_item_offset = (
                            pygame.Vector2(carried_item.rect.center)
                            - pygame.Vector2(person.rect.center)
                        )
                    dragging_sprite = None
            elif event.type == pygame.MOUSEMOTION:
                if agent.is_menu_open:
                    for button in agent.choice_buttons:
                        button.handle_event(event)
                if dragging_sprite:
                    if can_place_item(dragging_sprite, sprite_list):
                        # pygame.draw.rect(screen, pygame.Color(0,220,0,a=0), dragging_sprite.get_rect())
                        # draw_alpha_rect(screen, pygame.Color(0,220,0,a=50),  dragging_sprite.get_rect())
                        # pygame.display.flip()
                        highlight_color = pygame.Color(0, 220, 0, 50)
                        highlight_rect = dragging_sprite.get_rect()
                        
                        print("show green")
                    elif not can_place_item(dragging_sprite, sprite_list):
                        highlight_color = pygame.Color(220, 0, 0, 50)
                        highlight_rect = dragging_sprite.get_rect()
                        print("show red here")
                    dragging_sprite.drag(event.pos)
                if not dragging_sprite and not agent.is_menu_open:
                    menu_manager.motion(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    agent.call()
                elif event.key == pygame.K_e and carried_item is not None:
                    unsatisfied = get_unsatisfied_prerequisites(carried_item, sprite_list)
                    metrics.record_placement_attempt(
                        carried_item,
                        "human",
                        unsatisfied,
                    )
                    if carried_item.check_stop() and can_place_item(carried_item, sprite_list):
                        carried_item.rect.topleft = carried_item.goal
                        carried_item.snapped = True
                        metrics.record_placement_success(carried_item, "human")
                        carried_item.stop_drag()
                        carried_item = None
                        carried_item_offset = pygame.Vector2(0, 0)
                        highlight_rect = None
                    else:
                        metrics.record_placement_failure(
                            carried_item, "human", unsatisfied
                        )
                        menu_manager.open_menu(carried_item.show_box())
                        carried_item.stop_drag()
                        pickup_blocked_item = carried_item
                        carried_item.send_to_spawn()
                        carried_item = None
                        carried_item_offset = pygame.Vector2(0, 0)
                        highlight_rect = None
                elif event.key ==pygame.K_t and carried_item is not None:
                    metrics.record_cancellation(carried_item, source="T_key")
                    menu_manager.open_menu(carried_item.show_box2())
                    carried_item.stop_drag()
                    pickup_blocked_item = carried_item
                    carried_item.send_to_spawn()
                    carried_item = None
                    carried_item_offset = pygame.Vector2(0, 0)
                    highlight_rect = None
                elif event.key == pygame.K_ESCAPE:
                    agent.cancel_choice()

        keys = pygame.key.get_pressed()
        movement = pygame.Vector2(
            keys[pygame.K_d] - keys[pygame.K_a],
            keys[pygame.K_s] - keys[pygame.K_w],
        )
        player_moving = movement.length_squared() > 0
        if player_moving:
            movement = movement.normalize() * PLAYER_SPEED * dt
            person.rect.x += round(movement.x)
            person.rect.y += round(movement.y)
            out_of_bounds = person.rect.x >= 600 and person.rect.y <= 600
            person.rect.clamp_ip(PLAYER_BOUNDS)

            if out_of_bounds:
                person.rect.x -= 100

        person_center = pygame.Vector2(person.rect.center)
        if pickup_blocked_item is not None:
            blocked_distance = (
                pygame.Vector2(pickup_blocked_item.rect.center) - person_center
            ).length()
            if blocked_distance > PLAYER_PICKUP_RADIUS + 25:
                pickup_blocked_item = None

        if carried_item is None and pickup_blocked_item is None:
            nearby_items = [
                sprite
                for sprite in sprite_list
                if sprite not in {person, robot}
                and not getattr(sprite, "snapped", False)
                and (
                    pygame.Vector2(sprite.rect.center) - person_center
                ).length() <= PLAYER_PICKUP_RADIUS
            ]
            if nearby_items:
                carried_item = min(
                    nearby_items,
                    key=lambda sprite: (
                        pygame.Vector2(sprite.rect.center) - person_center
                    ).length_squared(),
                )
                metrics.record_pickup(carried_item)
                carried_item_offset = (
                    pygame.Vector2(carried_item.rect.center) - person_center
                )

        if carried_item is not None:
            carried_item.rect.center = person_center + carried_item_offset
            highlight_rect = carried_item.get_rect()
            if can_place_item(carried_item, sprite_list):
                highlight_color = pygame.Color(0, 220, 0, 50)
            else:
                highlight_color = pygame.Color(220, 0, 0, 50)

        agent.update(dt)

        now = time.perf_counter()
        metrics.record_frame(now=now, player_moving=player_moving)
        if check_task_complete(items_by_name) and not metrics.finalized:
            metrics.finalize(completed=True, now=now)

        mouse_x, mouse_y = pygame.mouse.get_pos()
        out_of_bounds = mouse_x >= 600 and mouse_y <= 600

        
        if out_of_bounds and menu_manager.active_menu is None:
            menu_manager.open_menu(Notibox)
            if dragging_sprite:
                dragging_sprite.stop_drag()
                dragging_sprite = None
        elif not out_of_bounds and menu_manager.active_menu is Notibox:
            menu_manager.close_active_menu()

        # screen.fill((156, 148, 146))
        screen.blit(BackGround.image, BackGround.rect)
        draw_pickup_area(screen, person.rect.center, PLAYER_PICKUP_RADIUS)

        # blues1 = pygame.draw.rect(screen, (0, 0, 255), (0, 600, 1200, 250), width=2, border_radius=-1)
        # pygame.draw.rect(screen, (0, 0, 0), (0, 0, 600, 600), width=2, border_radius=-1)
        pygame.draw.rect(screen, (255, 0, 0), (600, 0, 600, 600), width=2, border_radius=-1)

        sprite_list.update()
        sprite_list.draw(screen)
        if highlight_rect:
            draw_alpha_rect(screen, highlight_color, highlight_rect)
        agent.draw_choice_buttons(screen)
        menu_manager.display()
    
        pygame.display.flip()

    metrics.finalize(completed=check_task_complete(items_by_name))



if __name__ == "__main__":
    main()
    pygame.quit()