from django.conf.urls.defaults import *

urlpatterns = patterns('usginvalid.views',
    url(r'^rule/(?P<pk>[0-9]+)/?$', 'rule_view'),
    url(r'^ruleset/(?P<pk>[0-9]+)/?$', 'ruleset_view')
)