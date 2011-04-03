import re
from django.contrib import admin
from django import forms
from models import XPath, ValidValue, Rule, RuleSet, ValidValuesSet
from django.core.exceptions import ValidationError

class XPathInline(admin.TabularInline):
    model = XPath
    
class ValidValueInline(admin.TabularInline):
    model = ValidValue

class ValidValueSetAdmin(admin.ModelAdmin):
    list_display = ('name', 'values_preview')
    
    inlines = [ValidValueInline]
        
class RuleAdminForm(forms.ModelForm):
    class Meta:
        model = Rule
        
    def clean(self):
        # Here is where I can catch XPath quantity issues, which depend on the type of 
        #  Rule that is being created/updated
        xpath_count = 0
        for index in self.data:
            if re.match('^xpath_set-[0-9]+-xpath', index) != None:
                if self.data[index] != '': xpath_count = xpath_count + 1
        
        # Model has not been validated yet. Need to make sure that the Type has been specified
        if self.cleaned_data['type'] == None:
            raise ValidationError('Please specify the type of rule you wish to create')
        
        if self.cleaned_data['type'] in ['ExistsRule', 'ValueInListRule', 'ContentMatchesExpressionRule'] and xpath_count != 1:
            raise ValidationError('Exactly one XPath is allowed')
        if self.cleaned_data['type'] in ['AnyOfRule', 'OneOfRule'] and xpath_count < 2:
            raise ValidationError('Any of and One of Rules must have at least two XPaths.')
        if self.cleaned_data['type'] == 'ConditionalRule' and xpath_count > 0:
            raise ValidationError('Conditional Rules do not use any XPaths.')
        
        return self.cleaned_data
    
class RuleAdmin(admin.ModelAdmin):
    class Media:
        css = {
            "all": ("usginvalid/css/base-admin-adjustments.css",)
        }
        
    form = RuleAdminForm
    
    list_display = ('name', 'description', 'type')
    list_filter = ('type', )
    list_per_page = 25
    search_fields = ['name', 'description']
    
    fieldsets = [
                ('Required Information', {
                    'fields': ['name', 'description', 'type'],
                    'description': 'The following fields are required for all rules.'
                    }
                ),
                ('Rule-Type Specific Fields', {
                    'fields': ['values', 'regex', ('condition_rule', 'requirement_rule')],
                    'description': 'The following fields are required for rules of some specific type'
                    }
                )
    ]
    
    inlines = [XPathInline]

class RuleSetAdmin(admin.ModelAdmin):
    class Media:
        css = {
            "all": ("usginvalid/css/base-admin-adjustments.css",)
        }
        
    list_display = ('name', 'purpose')
    #filter_vertical = ['rules']   
     
admin.site.register(RuleSet, RuleSetAdmin)
admin.site.register(ValidValuesSet, ValidValueSetAdmin)
admin.site.register(Rule, RuleAdmin)