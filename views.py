from django.shortcuts import get_list_or_404
from django.http import HttpResponse
from django.core import serializers
from models import Rule, RuleToRuleSetLink

def rule_view(request, pk):
    rule = get_list_or_404(Rule, pk=pk)
    response = serializers.serialize('json', rule)
    return HttpResponse(response, mimetype='application/json')