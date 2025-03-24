import os
from typing import List, Tuple
from pathlib import Path
import httpx
from my_logger import configure_logger
from dataclasses import dataclass, field


@dataclass
class Project:
    """A class representing a project.

    Attributes:
        name (str): The name of the project.
        category (str): The category the project falls under.
    """

    name: str
    category: str


@dataclass
class JiraClient:
    """A class representing a Jira API client.

    Attributes:
        server_url (str): The URL of the Jira server.
        username (str): The username to authenticate with.
        password (str): The password to authenticate with.
        endpoint (str): The API endpoint to use (default: "/rest/api/2/project").
        headers (dict): Additional headers to send with requests (default: {"Content-Type": "application/json"}).
    """

    server_url: str
    username: str
    password: str
    endpoint: str = "/rest/api/2/project"
    headers: dict = field(default_factory=lambda: {"Content-Type": "application/json"})

    def __post_init__(self):
        """Initialize the client."""

        self.endpoint = self.server_url + self.endpoint

    def get_projects(self) -> List[Project]:
        """Get a list of projects from the Jira API.

        This method sends a GET request to the Jira API endpoint specified in the `endpoint` attribute
        and retrieves a list of project objects. Each project object contains information such as the
        project name and category.

        Returns:
            A list of `Project` objects representing the projects retrieved from the API.

        Raises:
            httpx.RequestError: If there is an error while sending the request or processing the response.
        """

        with httpx.Client(auth=(self.username, self.password), headers=self.headers) as client:
            try:
                response = client.get(self.endpoint)
                response.raise_for_status()
                projects_data = response.json()
            except httpx.RequestError as e:
                raise e
        projects = []
        for project_data in projects_data:
            if "projectCategory" in project_data:
                category_name = project_data["projectCategory"]["name"]
            else:
                category_name = "No category"
            projects.append(Project(project_data["name"], category_name))
        return projects


@dataclass
class ProjectCounter:
    """A utility class for counting projects by category.

    This class provides a method for counting the number of projects in the `projects` list
    that have a category and the number that do not have a category.

    Attributes:
        projects: A list of `Project` objects representing the projects to count.
    """

    projects: List[Project]

    def count_categories(self) -> Tuple[int, int]:
        """Count the number of projects by category.

        This method counts the number of projects in the `projects` list that have a category and
        the number that do not have a category.

        Returns:
            A tuple containing two integers:
            - The number of projects that have a category.
            - The number of projects that do not have a category.
        """
        project_category_counter = 0
        no_category_counter = 0
        for project in self.projects:
            if project.category != "No category":
                project_category_counter += 1
            else:
                no_category_counter += 1
        return project_category_counter, no_category_counter


class ProjectLogger:
    """A utility class for logging project information.

    This class provides methods for logging information about a project to a logger.

    Attributes:
        logger: A logger object to use for logging project information.
    """

    def __init__(self, logger) -> None:
        """Initialize a new `ProjectLogger` object.

        Args:
            logger: A logger object to use for logging project information.
        """

        self.logger = logger

    def log_project_info(self, project: Project) -> None:
        """Log information about a project.

        This method logs the name and category of a project to the logger.

        Args:
            project: A `Project` object representing the project to log.
        """

        self.logger.info(f"PROJECT NAME == {project.name}, PROJECT CATEGORY == {project.category}")

    def info(self, message: str) -> None:
        """Log a general information message.

        This method logs a general information message to the logger.

        Args:
            message: A string representing the information message to log.
        """

        self.logger.info(message)


class ProjectAnalyzer:
    def __init__(self, logger, server_url: str, username: str, password: str) -> None:
        """Initialize a ProjectAnalyzer object.

        Args:
            logger: A logger object to use for logging.
            server_url: The URL of the Jira server.
            username: The username to use for authentication.
            password: The password to use for authentication.
        """

        self.logger = logger
        self.client = JiraClient(server_url, username, password)
        self.projects = self.client.get_projects()
        self.counter = ProjectCounter(self.projects)
        self.logger = ProjectLogger(self.logger)

    def analyze(self) -> None:
        """Analyze the Jira projects and log the results.

        This method logs the name and category of each project using a ProjectLogger
        object, and then logs the total number of projects with categories, the total
        number of projects without categories, and the total number of projects.
        """

        project_category_count, no_category_count = self.counter.count_categories()

        for project in self.projects:
            self.logger.log_project_info(project)

        self.logger.info(
            f"Projects with category - {project_category_count}\nNo Category - "
            f"{no_category_count}\nAll Projects - {len(self.projects)}"
        )


def main() -> None:
    """
    The main function of the program which fetches the list
    of projects from the specified JIRA server,
    counts the number of projects with and without
    categories, and logs the details of all the projects.

    Returns:
        None
    """

    logger = configure_logger(Path(__file__).stem)
    server_url = os.getenv("j_prd_url")
    username = os.getenv("j_prd_us")
    password = os.getenv("j_prd_ps")

    analyzer = ProjectAnalyzer(logger, server_url, username, password)
    analyzer.analyze()


if __name__ == "__main__":
    main()
