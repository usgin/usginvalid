from django.db import models
from django.core.exceptions import ValidationError

class RuleSet(models.Model):
    name = models.CharField(max_length=255)
    purpose = models.CharField(max_length=255)
    rules = models.ManyToManyField('Rule')
    
    def __unicode__(self):
        return self.name

RULE_TYPES = (
              ('ExistsRule', 'XPath Exists'),
              ('ValueInListRule', 'XPath Value is Valid'),
              ('AnyOfRule', 'At Least One XPath From a Set Exists'),
              ('OneOfRule', 'Only One XPath From a Set Exists'),
              ('ContentMatchesExpressionRule', 'XPath Value Matches Regular Expression'),
              ('ConditionalRule', 'Conditional: Execute One Rule if Another is Valid'))
    
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
    
    def clean(self):
        # Make sure that only appropriate fields are populated depending on the type of rule
        # Model.clean does not yet have any information about xpath_set, so that validataion must
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