from django.conf.urls.defaults import *

urlpatterns = patterns('usginvalid.views',
    url(r'^rule/(?P<pk>[0-9]+)/?$', 'rule_view'),
    url(r'^ruleset/(?P<pk>[0-9]+)/((?P<format>.+)/)?$', 'ruleset_view'),
    url(r'^valueset/(?P<pk>[0-9]+)/?$', 'valueset_view')
)