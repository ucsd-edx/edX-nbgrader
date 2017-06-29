import json, os, urllib, subprocess, shutil
from bs4 import BeautifulSoup as bs


class DummyGrader:
    def __init__(self, grader_root=''):
        self.grader_root = grader_root

    def __call__(self, student_response):
        print 'received submission:', student_response
        return {'correct': True,  'score': 85,  'msg':  'Good work!'}


class SimpleGrader:
    def __init__(self, grader_root='/home/ubuntu/edX-extensions/edX-nbgrader/xqueue-watcher/dummy-course/'):
        """
        grader object
        :param grader_root: course directory
        """
        self.grader_root = grader_root

    @staticmethod
    def _handle_result(success, **kwargs):
        if not success:
            print kwargs['msg']
        return kwargs

    @staticmethod
    def _autograde(section_name):
        p = subprocess.Popen(["nbgrader", "autograde", section_name, "--student", "hacker"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        print "Out is: >>>\n{0}\n<<<".format(out)
        print "Err is: >>>\n{0}\n<<<".format(err)
        return out, err

    @staticmethod
    def _get_feedback(section_name):
        p = subprocess.Popen(["nbgrader", "feedback", section_name, "--student", "hacker"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        return out, err

    def _clean(self):
        shutil.rmtree(os.path.join(self.grader_root, 'submitted'))
        shutil.rmtree(os.path.join(self.grader_root, 'autograded'))
        shutil.rmtree(os.path.join(self.grader_root, 'feedback'))

    def grade(self, section_name, submission_url, problem_name='problem1'):
        # return vars
        correct = None
        score = None
        msg = ''

        if section_name != 'ps1':
            return SimpleGrader._handle_result(False, msg='Wrong section name.', correct=correct, score=score)

        os.chdir(self.grader_root)

        # TODO: error handling
        grading_dir = 'submitted/hacker/{}/'.format(section_name)
        feedback_html = 'feedback/hacker/{}/{}.html'.format(section_name, problem_name)

        # Download notebook
        notebook_name = '{}.ipynb'.format(problem_name)
        if not os.path.isdir(grading_dir):
            os.makedirs(grading_dir)
        try:
            with open(os.path.join(grading_dir, notebook_name), 'w') as f:
                for l in urllib.urlopen(submission_url):
                    f.write(l)
        except Exception as e:
            self._clean()
            return SimpleGrader._handle_result(False, msg=str(e), correct=correct, score=score)

        # grade and get feedback
        # TODO: more feedback?
        out, err = SimpleGrader._autograde(section_name)
        if 'AutogradeApp | ERROR' not in err:
            out, err = SimpleGrader._get_feedback(section_name)
        else:
            self._clean()
            return SimpleGrader._handle_result(False, msg=err, correct=correct, score=score)
        with open(feedback_html, 'r') as f:
            soup = bs(''.join(f.readlines()), 'html.parser')
        report = soup.body.div.div.div
        report = [line.strip() for line in report.prettify().split('\n') if line and not line.strip().startswith('<')]
        report = [l for l in report if not l.startswith('Comment')]

        score = float(report[0].split(' ')[-3])
        correct = score > 0
        msg = '<br />'.join(report)
        self._clean()
        return {'correct': correct, 'score': score, 'msg': msg}

    def __call__(self, student_response):
        xqueue_body = json.loads(student_response['xqueue_body'])
        problem_name = xqueue_body['grader_payload']
        submission_files = json.loads(student_response['xqueue_files'])
        submission_url = submission_files['problem1.ipynb']

        result = self.grade(problem_name, submission_url)
        return result
