import re, urllib2, datetime
from django.contrib import admin
from django import forms
from django.conf import settings
from models import XPath, ValidValue, Rule, RuleSet, ValidValuesSet, ValidationJob, ValidationReport, ValidationReportItem, ValidationSet
from django.core.exceptions import ValidationError
from BeautifulSoup import BeautifulSoup
from urlparse import urljoin, urlparse, ParseResult, urlunparse
from xmlvalidator import ValidationException
from lxml import etree

class RuleInline(admin.TabularInline):
    model = RuleSet.rules.through
    extra = 0
    fields = ['rule', 'rule_description', 'rule_type']
    readonly_fields = ['rule_description', 'rule_type']
    
class ValidationReportItemAdmin(admin.TabularInline):
    model = ValidationReportItem
    readonly_fields = ['item']
    can_delete = False
    max_num = 0
        
class ValidationJobInline(admin.TabularInline):
    model = ValidationJob
    fields = ['url', 'last_result']
    readonly_fields = ['url', 'last_result', 'last_report_link'] 
    can_delete = False
    max_num = 0
       
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
        #  rule that is being created/updated
        xpath_count = 0
        for index in self.data:
            if re.match('^xpath_set-[0-9]+-xpath', index) != None:
                if self.data[index] != '': xpath_count = xpath_count + 1
        
        # Model has not been validated yet. Need to make sure that the Type has been specified
        if self.cleaned_data['type'] == None:
            raise ValidationError('Please specify the type of rule you wish to create')
        
        if self.cleaned_data['type'] in ['ExistsRule', 'ValueInListRule', 'ContentMatchesExpressionRule', 'ValidUrlRule'] and xpath_count != 1:
            raise ValidationError('Exactly one XPath is allowed')
        if self.cleaned_data['type'] in ['AnyOfRule', 'OneOfRule'] and xpath_count < 2:
            raise ValidationError('Any of and One of Rules must have at least two XPaths.')
        if self.cleaned_data['type'] == 'ConditionalRule' and xpath_count > 0:
            raise ValidationError('Conditional Rules do not use any XPaths.')
        
        return self.cleaned_data
    
class RuleAdmin(admin.ModelAdmin):
    class Media:
        css = {
            "all": (settings.MEDIA_URL + "usginvalid/css/base-admin-adjustments.css",)
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
                    'fields': ['values', 'regex', 'context', ('condition_rule', 'requirement_rule')],
                    'description': 'The following fields are required for rules of some specific type'
                    }
                )
    ]
    
    inlines = [XPathInline]

class RuleSetAdmin(admin.ModelAdmin):
    class Media:
        css = {
            "all": (settings.MEDIA_URL + "usginvalid/css/base-admin-adjustments.css",
                    settings.MEDIA_URL + "usginvalid/css/ruleset-list.css")
        }
        js = (settings.MEDIA_URL + "usginvalid/js/jquery-1.4.4.min.js",
              settings.MEDIA_URL + "usginvalid/js/ruleset-list.js")
        
    list_display = ('name', 'purpose')

    exclude = ['rules']
    inlines = [RuleInline]

class ValidationJobAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'set_link', 'last_result', 'last_report_link']
    list_filter = ['set', 'last_result']
    search_fields = ['url', 'name']
    
    def save_model(self, request, obj, form, change):
        obj.save()
        
        result, report = obj.ruleset.xml_validate(obj.url)
        obj.last_result = result
        obj.save()
        
        new_report = obj.validationreport_set.create()
        new_report.save()
        
        for item in report:
            new_item = new_report.validationreportitem_set.create(item=item)
            new_item.save()
            
        if len(new_report.validationreportitem_set.all()) == 0:
            new_item = new_report.validationreportitem_set.create(item='Passed Validation Without Errors')
            new_item.save()
    
class ValidationReportAdmin(admin.ModelAdmin):
    readonly_fields = ['job', 'run_date']
    inlines = [ValidationReportItemAdmin]

def string_is_getrecords(response_string):
    result = False
    
    # Can lxml parse it?
    try:
        doc = etree.fromstring(response_string)
    except Exception, err:
        # lxml can't parse it. Not a valid csw response at least...
        pass
    else:
        if doc.tag == '{http://www.opengis.net/cat/csw/2.0.2}GetRecordsResponse':
            result = True
    return result

def construct_recordbyid_request(recordId, parsed_csw_url):
    query = 'request=GetRecordById&service=CSW&Id=' + recordId + '&elementSetName=full&outputSchema=http://www.isotc211.org/2005/gmd'
    url_builder = ParseResult(scheme=parsed_csw_url.scheme, 
                              netloc=parsed_csw_url.netloc, 
                              path=parsed_csw_url.path, 
                              params='', 
                              query=query, 
                              fragment='')
    return urlunparse(url_builder)
    
def file_list_from_csw(getrecords_string, url):
    '''
    Given a string representing a csw:GetRecords response
    Returns a list of tuples: (url to get an individual record, error message)
    '''
    
    doc = etree.fromstring(getrecords_string)
    ns = {'csw': 'http://www.opengis.net/cat/csw/2.0.2',
          'dc': 'http://purl.org/dc/elements/1.1/'} 
    # Get a list of records. Requires csw:BriefRecords
    records = doc.xpath('//csw:BriefRecord', namespaces=ns)
    
    if len(records) == 0:
        # There were no brief records. Maybe the request is bad, maybe there are just no records.
        error_message = 'No csw:BriefRecord elements found in csw:GetRecordsResponse.'
        return [('', error_message)]
    
    else:
        csw = urlparse(url)
        file_list = list()
        for record in records:
            # Finding the FileID might get tricky
            identifiers = record.xpath('dc:identifier', namespaces=ns)
            if len(identifiers) == 1:
                recordId = identifiers[0].text
                file_list.append((construct_recordbyid_request(recordId, csw), ''))
            else:
                # Find the ESRI-style file ID
                fileId = record.xpath('dc:identifier[@scheme="urn:x-esri:specification:ServiceType:ArcIMS:Metadata:FileID"]', namespaces=ns)
                if len(fileId) == 1: 
                    recordId = fileId[0].text
                    file_list.append((construct_recordbyid_request(recordId, csw), ''))
                else:
                    # Could look for other-style file IDs here
                    file_list.append(('','Could not find File Identifier in csw:BriefRecord.'))
        
        return file_list

def file_list_from_waf(response_string, url):
    '''
    Given a string representing a web-accessible folder's HTML
    Returns a list of tuples: (url to get an individual record, error message)
    '''
    #Soupify
    soup = BeautifulSoup(response_string)
    
    file_list = list()
    
    # Loop through all the links to XML files
    tags = soup.findAll('a', href=re.compile('.+\.xml'))
    for tag in tags:
        # Generate an absolute URL to the XML file
        file_list.append((urljoin(url, tag['href']), ''))
        
    return file_list
                        
class ValidationSetAdmin(admin.ModelAdmin):
    #inlines = [ValidationJobInline]
    
    def save_model(self, request, obj, form, change):
        # Save the Validation Set so we know we can create related objects from it
        obj.save()
        
        # Get the content at the given URL
        req = urllib2.Request(obj.url)
        response = urllib2.urlopen(req).read()
        
        if string_is_getrecords(response):
            files = file_list_from_csw(response, obj.url)
        else:
            files = file_list_from_waf(response, obj.url)
            
        # Now Validate them
        for file in files:
            if file[0] != '':    
                try:
                    result, report = obj.ruleset.xml_validate(file[0])
                except ValidationException, err:
                    result = False
                    report = ['Validation Error: '  + err.msg]
            else:
                result = False
                report = ['Parser error: ' + file[1]]
                
            # Find an old Job or create a new one
            existing = obj.validationjob_set.filter(name=file[0])
            if len(existing) > 0:
                new_job = existing[0]
                new_job.last_result = result
            else:    
                new_job = obj.validationjob_set.create(name=file[0], ruleset=obj.ruleset, url=file[0], last_result=result)
            new_job.save()
            
            # Create a new report
            new_report = new_job.validationreport_set.create(run_date=datetime.datetime.now())
            new_report.save()
            
            # Create report items
            for item in report:
                new_item = new_report.validationreportitem_set.create(item=item)
                new_item.save()
            
            if len(new_report.validationreportitem_set.all()) == 0:
                new_item = new_report.validationreportitem_set.create(item='Passed Validation Without Errors')
                new_item.save()
           
admin.site.register(RuleSet, RuleSetAdmin)
admin.site.register(ValidValuesSet, ValidValueSetAdmin)
admin.site.register(Rule, RuleAdmin)
admin.site.register(ValidationJob, ValidationJobAdmin)
admin.site.register(ValidationReport, ValidationReportAdmin)
admin.site.register(ValidationSet, ValidationSetAdmin)