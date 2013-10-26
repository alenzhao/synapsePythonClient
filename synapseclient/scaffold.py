"""
********************************
Scaffolding for Synapse Projects
********************************

"""
import pkg_resources
import re


from synapseclient import Project, Folder, File, Wiki
from synapseclient.utils import _to_list
from synapseclient.exceptions import SynapseHTTPError


def _slugify(a, max_length=18):
    """An over-simplified function to turn a string into a slug"""
    return re.sub('-+$', '',
            re.sub('-+', '-',
             re.sub('\W', '-', a.lower()))[0:max_length])

def _is_email(a):
    """Returns true if the string looks even vaguely like an email, false otherwise"""
    return bool(re.match("[^@]+@[^@]+\.[^@]+", a.strip()))


class Scaffold(object):

    def __init__(self, synapse):
        self.syn = synapse


    def _find_user(self, name):
        ## the following returns a dict w/ keys 'children' and 'totalNumberOfResults'
        ## 'children' contains a list of headers with 'displayName', 'isIndividual',
        ## 'ownerId' and a preview 'pic'
        return self.syn.restGET('/userGroupHeaders?prefix=%s' % name)


    def _create_or_update_wiki(self, owner, **kwargs):
        if 'title' in kwargs:
            for header in self.syn.getWikiHeaders(owner=owner):
                if kwargs['title']==header.title:
                    wiki = self.syn.getWiki(owner=owner, subpageId=header.id)
                    wiki.update(kwargs)
                    return self.syn.store(wiki)
        wiki = Wiki(owner=owner, **kwargs)
        return self.syn.store(wiki)


    def _contributor_markdown(self, contributor):

        ## helper function to flexibly get contributor's name
        def _name(contributor):
            return contributor.get('displayName', contributor.get('name',''))

        ## if given an email, look it up in synapse
        if isinstance(contributor, basestring):
            results = self._find_user(contributor)
            if results['totalNumberOfResults'] > 0:
                profile = self.syn.getUserProfile(results['children'][0]['ownerId'])
            else:
                profile = {'name':contributor}
        elif isinstance(contributor, int):
            profile = self.syn.getUserProfile(contributor)
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


    def _team_markdown(self, team):
        return '\n'.join(['* '+self._contributor_markdown(member) for member in team])


    def data_analysis(self, name, **kwargs):
        """
        Scaffold for a data analysis project

        :param name:         name your project
        :param team:         list of emails, names or synapse user IDs
        """
        project = self.syn.store(Project(name))

        data = self.syn.store(Folder('data', parent=project))
        code = self.syn.store(Folder('src', parent=project))
        figures = self.syn.store(Folder('figures', parent=project))

        if 'team' not in kwargs:
            team = [self.syn.getUserProfile(), 'Add team members']
        else:
            team = kwargs['team']

        template = pkg_resources.resource_string('synapseclient', 'templates/data_analysis.md.template')

        markdown = template.format(
                    name=name,
                    data_syn_id=data.id,
                    name_slug=_slugify(name),
                    code_syn_id=code.id,
                    figures_syn_id=figures.id,
                    team=self._team_markdown(team))

        wiki_top = self._create_or_update_wiki(owner=project, title=name, markdown=markdown)

        template = pkg_resources.resource_string('synapseclient', 'templates/data.md.template')
        markdown = template.format(data_syn_id=data.id)
        wiki_data = self._create_or_update_wiki(owner=project, title='Data', parentWikiId=wiki_top.id, markdown=markdown)

        template = pkg_resources.resource_string('synapseclient', 'templates/methods.md.template')
        markdown = template.format(code_syn_id=code.id)
        wiki_methods = self._create_or_update_wiki(owner=project, title='Methods', parentWikiId=wiki_top.id, markdown=markdown)

        template = pkg_resources.resource_string('synapseclient', 'templates/results.md.template')
        markdown = template.format(figures_syn_id=figures.id)
        wiki_results = self._create_or_update_wiki(owner=project, title='Results', parentWikiId=wiki_top.id, markdown=markdown)

        entities = {}
        for key, folder in (('data', data), ('code', code), ('figures', figures)):
            entities[key] = []
            if key in kwargs:
                for filepath in _to_list(kwargs[key]):
                    entities[key].append(
                        self.syn.store(File(filepath, parent=folder)))

        return project


