from django.contrib import admin
from models import XPath, ValidValue, Rule, RuleSet, ValidValuesSet

class XPathInline(admin.TabularInline):
    model = XPath
    
class ValidValueInline(admin.TabularInline):
    model = ValidValue

class ValidValueSetAdmin(admin.ModelAdmin):
    inlines = [ValidValueInline]
        
class RuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'type')
    list_filter = ('type', )
    list_per_page = 25
    search_fields = ['name', 'description']
    
    fieldsets = [
                 ('Required Information', {
                                           'fields': ['name', 'description', 'type'],
                                           'description': 'The following fields are required for all rules.'
                                           }
                 )
                 ('Rule-Type Specific Fields', {
                                            'fields': ['values', 'regex', ('condition_rule', 'requirement_rule')],
                                            'description': 'The following fields are required for rules of some specific type'}
                 )
                ]
    
    inlines = [XPathInline]

admin.site.register(RuleSet)
admin.site.register(ValidValuesSet, ValidValueSetAdmin)
admin.site.register(Rule, RuleAdmin)