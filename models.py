import requests
import json
from collections import defaultdict
from functools import partial


def _get_value(key, values):
    keys = key.split('.') if type(key) == str else key
    values = [values] if type(values) != list else values

    skey = keys.pop(0)
    for value in values:
        if skey in value:
            return _get_value(keys, value[skey]) if keys else value[skey]


class Build(object):
    def __init__(self, build):
        self.build = build

    def get_value(self, key):
        return _get_value(key, self.build)

    def __getattr__(self, item):
        return getattr(self.build, item)

    def __getitem__(self, item):
        return self.build.get(item)

    def __repr__(self):
        return json.dumps(self.build, indent=2)


class BaseJobView(object):

    def __init__(self, jenkins, name):
        self.jenkins = jenkins
        self.name = name
        self.type = self.__class__.__name__.lower()

    def _get(self, resource):
        """Get JSON from Jenkins CI"""
        base_url = self.jenkins.url.rstrip('/')
        return requests.get(base_url + resource).json()

    def get(self, depth=1):
        if self.type == 'job':
            res = self._get('/job/%s/api/json?depth=%s' % (self.name, depth))
            res['builds'] = [Build(build) for build in res['builds']]
        else:
            res = self._get('/view/%s/api/json?depth=%s' % (self.name, depth))
        return res


class Job(BaseJobView):
    def __init__(self, *args, **kwargs):
        self.filters = kwargs.pop('filters', {})
        super(Job, self).__init__(*args, **kwargs)

    def check_function(self, build, filters=None):
        filters = filters or self.filters
        if not filters:
            return True

        # check for actions parameters
        actions_parameters = build.get_value('actions.parameters')
        for k, v in filters.items():
            if k.startswith('actions.parameters.'):
                new_k = filters.pop(k)[len('actions.parameters.'):]
                new_v = {
                    'name': new_k,
                    'value': v
                }
                print(new_v, new_v not in actions_parameters)
                if new_v not in actions_parameters:
                    return False
        # check for everything else
        return all(build.get_value(k) == v for k, v in filters.items())

    def fetch_latest(self, params=None):
        params = params or {}
        data = self.get()
        for build in data['builds']:
            if build['building']:  # skip running
                continue
            if self.check_function(build, params):
                return dict(build_id=int(build['id']), result=build['result'],
                            url=self.jenkins.url+'/job/' + self.name + '/' + build['id'])
        return None


class View(BaseJobView):
    def fetch_latest(self, **params):
        pass


class JDefaultDict(defaultdict):
    def __missing__(self, key):
        ret = self[key] = self.default_factory(key)
        return ret


class JenkinsApi(object):
    def __init__(self, url, username='', api_key=''):
        self.url = url
        self.username = username
        self.api_key = api_key
        self.jobs = JDefaultDict(partial(Job, self))
        self.views = JDefaultDict(partial(View, self))
