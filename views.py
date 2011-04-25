from django.shortcuts import get_list_or_404, get_object_or_404, render_to_response
from django.http import HttpResponse
from django.core import serializers
from models import Rule, RuleToRuleSetLink, RuleSet, ValidValuesSet, ValidValue

def rule_view(request, pk):
    rule = get_list_or_404(Rule, pk=pk)
    response = serializers.serialize('json', rule)
    return HttpResponse(response, mimetype='application/json')

def serialize_rule(rule):
    if rule.type in ['ExistsRule', 'ValidUrlRule']:
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
                  'xpaths': rule.xpath_set.all(),
                  'context': rule.context}
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
    
    return render_to_response('usginvalid/ruleset.html', {'ruleset': ruleset, 'rules': rules})

def valueset_view(request, pk):
    valueset = get_object_or_404(ValidValuesSet, pk=pk)
    values = get_list_or_404(ValidValue, set=valueset)
    return render_to_response('usginvalid/valueset.html', {'valueset': valueset, 'values': values})