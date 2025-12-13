"""DAG construction utilities.

The DAG builder keeps a minimal surface area: it stores named tasks, validates
dependencies, and produces an execution order via topological sort with cycle
detection. Execution is delegated to the `Executor` to keep concerns separate.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Set

from src.core.logger import get_logger


@dataclass
class Task:
    """A unit of work in the DAG."""

    name: str
    func: Callable
    retries: int = 0
    description: str = ""


class DAGBuilder:
    def __init__(self, logger_name: str = __name__):
        self.tasks: Dict[str, Task] = {}
        self.dependencies: Dict[str, List[str]] = {}
        self.logger = get_logger(logger_name)

    def add_task(self, task: Task) -> None:
        if task.name in self.tasks:
            raise ValueError(f"Task '{task.name}' already exists.")
        self.tasks[task.name] = task
        self.dependencies[task.name] = []
        self.logger.debug("Registered task '%s'", task.name)

    def add_dependency(self, task_name: str, dependency_name: str) -> None:
        if task_name not in self.tasks:
            raise ValueError(f"Task '{task_name}' not found.")
        if dependency_name not in self.tasks:
            raise ValueError(f"Dependency '{dependency_name}' not found.")
        self.dependencies[task_name].append(dependency_name)
        self.logger.debug("Added dependency '%s' -> '%s'", dependency_name, task_name)

    def _visit(self, task_name: str, visiting: Set[str], visited: Set[str], order: List[str]) -> None:
        if task_name in visiting:
            raise ValueError(f"Cycle detected at task '{task_name}'.")
        if task_name in visited:
            return

        visiting.add(task_name)
        for dependency in self.dependencies.get(task_name, []):
            self._visit(dependency, visiting, visited, order)
        visiting.remove(task_name)

        visited.add(task_name)
        order.append(task_name)

    def get_execution_order(self) -> List[str]:
        """Return a topologically sorted list of task names."""

        visited: Set[str] = set()
        visiting: Set[str] = set()
        order: List[str] = []

        for task_name in self.tasks:
            if task_name not in visited:
                self._visit(task_name, visiting, visited, order)

        self.logger.debug("Resolved execution order: %s", order)
        return order