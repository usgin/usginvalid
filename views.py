from django.shortcuts import get_list_or_404, get_object_or_404, render_to_response
from django.template.loader import render_to_string
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
                  'values_pk': rule.values.pk,
                  'values': list(item.encode('ASCII') for item in rule.values.values_list())}
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

def clean_xpaths_list(rule):
    if 'xpaths' in rule:
        rule['xpaths'] = list(item.xpath for item in rule['xpaths'])
    return rule
    
def ruleset_view(request, pk, format=None):
    ruleset = get_object_or_404(RuleSet, pk=pk)
    rules = list()
    for rule in ruleset.rules.all():
        rules.append(serialize_rule(rule))
    
    if format == 'list':
        types = {'ExistsRule': 'usginvalid/exists.txt',
                 'ValueInListRule': 'usginvalid/valid-value.txt',
                 'ValidUrlRule': 'usginvalid/valid-url.txt',
                 'AnyOfRule': 'usginvalid/any-of.txt',
                 'OneOfRule': 'usginvalid/one-of.txt',
                 'ContentMatchesExpressionRule': 'usginvalid/regex.txt',
                 'ConditionalRule': 'usginvalid/condition.txt'}
        result = 'ruleset = list()\n'
        for rule in rules:
            rule = clean_xpaths_list(rule)
            if rule['type'] == 'ConditionalRule':
                rule['condition'] = clean_xpaths_list(rule['condition'])
                rule['requirement'] = clean_xpaths_list(rule['requirement'])
                result += render_to_string(types[rule['condition']['type']], {'rule': rule['condition'], 'name': 'condition'})
                result += render_to_string(types[rule['requirement']['type']], {'rule': rule['requirement'], 'name': 'requirement'})
                
            result += render_to_string(types[rule['type']], {'rule': rule, 'name': 'rule'})
        
        return HttpResponse(result, mimetype='text/plain')
    
    return render_to_response('usginvalid/ruleset.html', {'ruleset': ruleset, 'rules': rules})

def valueset_view(request, pk):
    valueset = get_object_or_404(ValidValuesSet, pk=pk)
    values = get_list_or_404(ValidValue, set=valueset)
    return render_to_response('usginvalid/valueset.html', {'valueset': valueset, 'values': values})