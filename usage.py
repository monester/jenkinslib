from cidashboard.jenkins import *
j = JenkinsApi('https://ci.fuel-infra.org')
j.jobs['verify-fuel-web'].fetch_latest()

j.jobs['verify-fuel-web'].fetch_latest({'actions.causes.shortDescription': 'timer'})
j.jobs['verify-fuel-web'].fetch_latest({'actions.parameters.GERRIT_REFSPEC': 'refs/heads/master'})
j.jobs['verify-fuel-web'].fetch_latest({'result': 'SUCCESS'})
j.jobs['verify-fuel-web'].fetch_latest({'result': 'FAILURE'})
