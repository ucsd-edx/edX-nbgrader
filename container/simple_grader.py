import json, os, urllib, subprocess, shutil
from bs4 import BeautifulSoup as bs


class SimpleGrader:
    def __init__(self, grader_root='/app'):
        """
        grader object
        :param grader_root: course directory
        """
        self.grader_root = grader_root
        self.course_dir = os.path.join(grader_root, 'dummy-course')

    @staticmethod
    def _handle_result(success, **kwargs):
        if not success:
            print json.dumps(kwargs)
        return kwargs

    @staticmethod
    def _autograde(section_name):
        p = subprocess.Popen(["nbgrader", "autograde", section_name, "--student", "hacker"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        return out, err

    @staticmethod
    def _get_feedback(section_name):
        p = subprocess.Popen(["nbgrader", "feedback", section_name, "--student", "hacker"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        return out, err

    def _clean(self):
        for dir_name in ['submitted', 'autograded', 'feedback']:
            dir_path = os.path.join(self.course_dir, dir_name)
            if os.path.isdir(dir_path):
                shutil.rmtree(dir_path)

    def grade(self, section_name, submission_url, problem_name):
        # return vars
        correct = False
        score = 0
        msg = ''

        # if section_name != 'ps1':
        #     return SimpleGrader._handle_result(False, msg='Wrong section name.', correct=correct, score=score)

        os.chdir(self.course_dir)

        # Create working dir
        grading_dir = 'submitted/hacker/{}/'.format(section_name)
        if not os.path.isdir(grading_dir):
            os.makedirs(grading_dir)

        # Download notebook
        notebook_name = '{}.ipynb'.format(problem_name)
        try:
            with open(os.path.join(grading_dir, notebook_name), 'w') as f:
                for l in urllib.urlopen(submission_url):
                    f.write(l)
        except Exception as e:
            self._clean()
            return SimpleGrader._handle_result(False, msg=str(e), correct=correct, score=score)

        # grade
        out, err = SimpleGrader._autograde(section_name)
        if 'AutogradeApp | ERROR' not in err:
            out, err = SimpleGrader._get_feedback(section_name)
        else:
            self._clean()
            return SimpleGrader._handle_result(False, msg=err, correct=correct, score=score)

        # Get feedback
        # TODO: scores from DB
        feedback_html = 'feedback/hacker/{}/{}.html'.format(section_name, problem_name)
        with open(feedback_html, 'r') as f:
            soup = bs(''.join(f.readlines()), 'html.parser')
        report = soup.body.div.div.div
        report = [line.strip() for line in report.prettify().split('\n') if line and not line.strip().startswith('<')]
        report = [l for l in report if not l.startswith('Comment')]

        score = float(report[0].split(' ')[-3])
        correct = score > 0
        msg = '<br />'.join(report)
        self._clean()
        print {'correct': correct, 'score': score, 'msg': msg}
        return {'correct': correct, 'score': score, 'msg': msg}


if __name__ == '__main__':
    test = SimpleGrader('/home/ubuntu/edX-extensions/edX-nbgrader/container/')
    test.grade('ps1', 'https://google.com', 'problem1')
