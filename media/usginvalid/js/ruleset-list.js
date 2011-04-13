var ruleRow;
ruleTypes = {'ExistsRule': 'XPath Exists',
             'ValueInListRule': 'XPath Value is Valid',
             'AnyOfRule': 'At Least One XPath From a Set Exists',
             'OneOfRule': 'Only One XPath From a Set Exists',
             'ContentMatchesExpressionRule': 'XPath Value Matches Regular Expression',
             'ConditionalRule': 'Conditional: Execute One Rule if Another is Valid',
             'ValidUrlRule': 'Check that a URL can be resolved.'};

function selectCheck() {
	// Get all the select boxes on the page, apply a change event handler
	$("select").change( function() {
		// Find the "value" attribute of the selected option
		//  This is the pk for the rule that was selected
		pk = $(this).val();
		ruleRow = $(this).parent().parent();
		$.getJSON("/validation/rule/" + pk + "/", function(data) {
			// Parse the response
			type = data[0]["fields"]["type"];
			description = data[0]["fields"]["description"];
			
			// Apply values to the appropriate elements
			ruleRow.children(".rule_description").children("p").text(description);
			ruleRow.children(".rule_type").children("p").text(ruleTypes[type]);
		});
	})
}

$(document).ready( function() {
	// Find the "Add another Rule" button
	$(".add-row td a").click( function() { selectCheck(); } )
	// Get all the select boxes, apply functionality to them
	selectCheck();
});