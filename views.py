from django.shortcuts import get_list_or_404, get_object_or_404, render_to_response
from django.http import HttpResponse
from django.core import serializers
from models import Rule, RuleToRuleSetLink, RuleSet

def rule_view(request, pk):
    rule = get_list_or_404(Rule, pk=pk)
    response = serializers.serialize('json', rule)
    return HttpResponse(response, mimetype='application/json')

def serialize_rule(rule):
    if rule.type == 'ExistsRule':
        result = {'pk': rule.pk, 
                  'name': rule.name,
                  'type': rule.type,
                  'xpath': rule.xpath_set.all()[0].xpath}
    if rule.type == 'ValueInListRule':
        result = {'pk': rule.pk,
                  'name': rule.name,
                  'type': rule.type, 
                  'xpath': rule.xpath_set.all()[0].xpath,
                  'values_name': rule.values.name,
                  'values_pk': rule.values.pk}
    if rule.type in ['AnyOfRule', 'OneOfRule']:
        result = {'pk': rule.pk,
                  'name': rule.name, 
                  'type': rule.type, 
                  'xpaths': rule.xpath_set.all()}
    if rule.type == 'ContentMatchesExpressionRule':
        result = {'pk': rule.pk,
                  'name': rule.name, 
                  'type': rule.type, 
                  'xpath': rule.xpath_set.all()[0].xpath,
                  'expression': rule.regex}
    if rule.type == 'ConditionalRule':
        result = {'pk': rule.pk,
                  'name': rule.name, 
                  'type': rule.type,
                  'condition': serialize_rule(rule.condition_rule),
                  'requirement': serialize_rule(rule.requirement_rule)}
    return result
    
def ruleset_view(request, pk):
    ruleset = get_object_or_404(RuleSet, pk=pk)
    rules = list()
    for rule in ruleset.rules.all():
        rules.append(serialize_rule(rule))
    
    #rules = [{'name': 'The name', 'type': 'The Type', 'xpath': 'The xpath'}]
    
    return render_to_response('usginvalid/ruleset.html', {'ruleset': ruleset, 'rules': rules})