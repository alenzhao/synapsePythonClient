"""
********************************
Scaffolding for Synapse Projects
********************************

"""
from synapseclient import Project, Folder, File, Wiki
from synapseclient.utils import _to_list
from collections import namedtuple


Contributor = namedtuple('Contributor', ['name', 'email', 'role'])


def findUser(name):
    ## the following returns a dict w/ keys 'children' and 'totalNumberOfResults'
    ## 'children' contains a list of headers with 'displayName', 'isIndividual',
    ## 'ownerId' and a preview 'pic'
    return syn.restGET('/userGroupHeaders?prefix=%s' % name)

def _is_email(a):
    """Returns true if the string looks even vaguely like an email, false otherwise"""
    return bool(re.match("[^@]+@[^@]+\.[^@]+", a.strip()))

def contributor_markdown(contributor):
    def _name(contributor):
        return contributor.get('displayName', contributor.get('name',''))

    ## if given an email, look it up in synapse
    if isinstance(contributor, basestring):
        results = findUser(contributor)
        if results['totalNumberOfResults'] > 0:
            profile = syn.getUserProfile(results['children'][0]['ownerId'])
        else:
            profile = {'name':contributor}
    else:
        profile = contributor

    ## profiles should have:
    ## 'displayName' or 'name', 'company', 'position', 'ownerId', 'url'

    fields = []
    if 'ownerId' in profile:
        fields.append("[%s](https://www.synapse.org/#!Profile:%s)" % (_name(profile), profile['ownerId']))
    elif 'url' in profile:
        fields.append("[%s](%s)" % (_name(profile), profile['url']))
    else:
        fields.append(_name(profile))

    if 'role' in profile:
        fields.append(profile['role'])
    elif 'position' in profile:
        fields.append(profile['position'])

    return ' '.join(fields)

def team_markdown(team):
    return '\n'.join(['* '+contributor_markdown(member) for member in team])

def data_analysis_project(name, **kwargs):
    """
    """
    project = syn.store(Project(name))

    data = syn.store(Folder('data', parent=project))
    code = syn.store(Folder('src', parent=project))
    figures = syn.store(Folder('figures', parent=project))

    if 'team' not in kwargs:
        team = [syn.getUserProfile(), 'Other team members?']
    else:
        team = kwargs['team']

    markdown = """
    #%s
    
    This is a template for a data analysis project. It would be great to add
    an overview and a bit of background to help readers understand the goals
    and methods of the project.

    ${image?synapseId=syn2280523&align=None&scale=100}

    ##Data
    The structure and limitations of the data (%s).

    ##Methods
    Analysis workflow, techniques and source code (%s).

    ##Results
    Findings and figures (%s).

    ##Team
    %s

    ##Links
    To publications, organization, data providers, funders, etc.

    """ % (name, data.id, code.id, figures.id, team_markdown(team))

    wiki = syn.store(Wiki(
        title=name,
        owner=project,
        markdown=markdown))

    entities = {}
    for key, folder in (('data', data), ('code', code), ('figures', figures)):
        entities[key] = []
        if key in kwargs:
            for filepath in _to_list(kwargs[key]):
                entities[key].append(
                    syn.store(File(filepath, parent=folder)))

