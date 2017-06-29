import sys
from simple_grader import SimpleGrader


grader = SimpleGrader('/app')


if __name__ == "__main__":
    [section_name, problem_name, submission_url] = sys.argv[1:]
    grader.grade(section_name, submission_url, problem_name)
