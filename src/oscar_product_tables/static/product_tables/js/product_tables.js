 
/* This is only used for the Table Product view */


function getForm(td){
	/* Fetches the form for this field and replaces the field on success */
	var tr = td.parent();
	var th = td.closest('table').find('th').eq(td.index());
	var productid = tr.data('productid');
	var code = th.data('code');
	var url = ajaxFormUrl + productid + '/' + code + '/';
	$.ajax({
		type: "GET",
		url: url,
		success: function(data) {
			td.html(data);
			td.attr('onclick_inactive', td.attr('onclick'));
			td.removeAttr('onclick');

		}
	}).done(function(){
			var form = td.find('form');
			var field = form.find('.form-control').first();
			if (field.is('select')){
				field.select2();
			}else{
				field.select();
			}
	});
}


function submitButtonClicked(button, action){
    var form = button.closest('form');
	var url = form.attr('action') + action + '/';
	submitFormToUrl(form, url);
}


function submitFormToUrl(form, url){
	/* Submits the form when valid and replaces it by the replaced value */
	var td = form.parent();
	
	$.ajax({
		type: "POST",
		url: url,
		data: form.serialize(),
		success: function(data) {
			td.html(data);
			td.attr('onclick', td.attr('onclick_inactive'));
			td.removeAttr('onclick_inactive');
		},
	});
}


function createListeners(){
	/* Listen to lazy-submit-form and lazy-get-form */
	getFormListener();
	submitFormListener();
}
