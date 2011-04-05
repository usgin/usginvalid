from django.db import models
from django.core.exceptions import ValidationError
from xmlvalidator import *

class RuleSet(models.Model):
    name = models.CharField(max_length=255)
    purpose = models.CharField(max_length=255)
    rules = models.ManyToManyField('Rule', through='RuleToRuleSetLink')
    
    def __unicode__(self):
        return self.name
    
    def rule_list(self):
        result = list()
        for rule in self.rules.all():
            result.append(rule.rule())
            
        return result
    
    def validate(self, filepath):
        result, report = record_is_valid(filepath, self.rule_list())
        return result, report
    
RULE_TYPES = (
              ('ExistsRule', 'XPath Exists'),
              ('ValueInListRule', 'XPath Value is Valid'),
              ('AnyOfRule', 'At Least One XPath From a Set Exists'),
              ('OneOfRule', 'Only One XPath From a Set Exists'),
              ('ContentMatchesExpressionRule', 'XPath Value Matches Regular Expression'),
              ('ConditionalRule', 'Conditional: Execute One Rule if Another is Valid'))

class RuleToRuleSetLink(models.Model):
    class Meta:
        ordering = ['rule_name']
        verbose_name = 'Rule'
        
    ruleset = models.ForeignKey('RuleSet')
    rule = models.ForeignKey('Rule')
    rule_description = models.CharField(max_length=255, blank=True)
    rule_type = models.CharField(max_length=255, choices=RULE_TYPES, blank=True)
    rule_name = models.CharField(max_length=255, blank=True)
    
    def __unicode__(self):
        return ''
    
    def clean(self):
        # Duplicate the required Rule information for use on the inline form
        self.rule_description = self.rule.description
        self.rule_type = self.rule.type
        self.rule_name = self.rule.name
        
class Rule(models.Model):
    class Meta:
        ordering = ['name']
        
    # Required Fields
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    type = models.CharField(max_length=255, choices=RULE_TYPES)
    
    # Remaining fields are optional, but may be required by clean method depending on type
    regex = models.CharField(max_length=2000, blank=True,
                             help_text='Matches Regular Expression Rule Only: Write the regular expression that should be matched.')
    values = models.ForeignKey('ValidValuesSet', blank=True, null=True,
                               help_text='Value is Valid Rules Only: Select or create a set of valid values.') 
    condition_rule = models.ForeignKey('Rule', blank=True, null=True,
                                       help_text='Conditional Rules Only: This is the prerequisite. If this rule validates, then the requirement must also validate. Should this rule fail to validate, the document does not fail the Conditional Rule.',
                                       related_name='condition')
    requirement_rule = models.ForeignKey('Rule', blank=True, null=True,
                                         help_text='Conditional Rules Only: This rule must be valid if the condition rule is valid.',
                                         related_name='requirement')
    
    def __unicode__(self):
        return self.name
    
    def xpath_list(self):
        return self.xpath_set.all().values_list('xpath', flat=True)
        
    def rule(self):
        if self.type == 'ExistsRule': 
            return ExistsRule(self.name, self.description, self.xpath_list()[0])
        if self.type == 'ValueInListRule':
            return ValueInListRule(self.name, self.description, self.xpath_list()[0], self.values.values_list())
        if self.type == 'AnyOfRule':
            return AnyOfRule(self.name, self.description, self.xpath_list())
        if self.type == 'OneOfRule':
            return OneOfRule(self.name, self.description, self.xpath_list())
        if self.type == 'ContentMatchesExpressionRule':
            return ContentMatchesExpressionRule(self.name, self.description, self.xpath_list()[0], self.regex)
        if self.type == 'ConditionalRule':
            return ConditionalRule(self.name, self.description, [self.condition_rule.rule(), self.requirement_rule.rule()])
            
    def clean(self):
        # Make sure that only appropriate fields are populated depending on the type of rule
        # Model.clean does not yet have any information about xpath_set, so that validation must
        #  be done through validation of the submitted form, not the rule itself. See RuleAdminForm in admin.py.
        if self.type == 'ExistsRule':
            if self.regex != '':
                raise ValidationError('Exists Rules do not use regular expressions')
            if not (self.condition_rule == None or self.requirement == None):
                raise ValidationError('Exists Rules do not use condition and requirement rules')
            if self.values != None:
                raise ValidationError('Exists Rules do not use a list of valid values')
        if self.type == 'ValueInListRule':
            if self.regex != '':
                raise ValidationError('Value is Valid Rules do not use regular expressions')
            if not (self.condition_rule == None or self.requirement == None):
                raise ValidationError('Value is Valid Rules do not use condition and requirement rules')
            if self.values == None:
                raise ValidationError('Value is Valid Rules require a list of valid values')
        if self.type == 'AnyOfRule' or self.type == 'OneOfRule':
            if self.regex != '':
                raise ValidationError('Any of and One of Rules do not use regular expressions')
            if not (self.condition_rule == None or self.requirement == None):
                raise ValidationError('Any of and One of Rules do not use condition and requirement rules')
            if self.values != None:
                raise ValidationError('Any of and One of Rules do not use a list of valid values')
        if self.type == 'ContentMatchesExpressionRule':
            if self.regex == '':
                raise ValidationError('Value Matches Regular Expression Rules require a regular expression')
            if not (self.condition_rule == None or self.requirement == None):
                raise ValidationError('Value Matches Regular Expression Rules do not use condition and requirement rules')
            if self.values != None:
                raise ValidationError('Value Matches Regular Expression Rules do not use a list of valid values')
        if self.type == 'ConditionalRule':
            if self.regex != '':
                raise ValidationError('Conditional Rules do no use regular expressions')
            if self.condition_rule == None or self.requirement == None:
                raise ValidationError('Conditional Rules require both a condition and a requirement rule')
            if self.values != None:
                raise ValidationError('Conditional Rules do not use a list of valid values')
            
class XPath(models.Model):
    xpath = models.CharField(max_length=2000)
    rule = models.ForeignKey('Rule')
    
    def __unicode__(self):
        return self.xpath

class ValidValuesSet(models.Model):
    class Meta:
        ordering = ['name']
        
    name = models.CharField(max_length=255)
    
    def __unicode__(self):
        return self.name
    
    def values_list(self):
        return self.validvalue_set.all().values_list('value', flat=True)
    
    def values_preview(self):
        list = self.values_list()
        result = ', '.join(['%s' % value for value in list])
        if len(result) > 28: result = result[:25] + '...'
        return result
             
class ValidValue(models.Model):
    class Meta:
        ordering = ['value']
        
    value = models.CharField(max_length=255)
    set = models.ForeignKey('ValidValuesSet')
    
    def __unicode__(self):
        return self.value