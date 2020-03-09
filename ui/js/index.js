$(function(){
    var devices = undefined;

    function showHideFormFields() {
        var security = $(this).find(':selected').attr('data-security');
        // start off with all fields hidden
        $('#service-group').addClass('hidden');
        $('#protoport-group').addClass('hidden');
        if(security === 'NONE') {
            return; // nothing to do
        }
        if(security === 'ENTERPRISE') {
            $('#service-group').removeClass('hidden');
            $('#protoport-group').removeClass('hidden');
            return;
        }
    }

    $('#bt_addr-select').change(showHideFormFields);

    $.get("/pincode", function(data){
        if(data.length !== 0){
            $('#pincode').val(data);
        } else {
            $('.reg-row').hide(); // no reg code, so hide that part of the UI
	}
    });

    $.get("/devices", function(data){
        if(data.length === 0){
            $('.before-submit').hide();
            $('#no-devices-message').removeClass('hidden');
        } else {
            devices = JSON.parse(data);
            $.each(devices, function(bt_addr, name){
                $('#bt_addr-select').append(
                    $('<option>')
                        .text(name)
                        .attr('val', bt_addr)
                        //.attr('data-security', val.security.toUpperCase())
                );
            });

            jQuery.proxy(showHideFormFields, $('#bt_addr-select'))();
        }
    });

    $('#connect-form').submit(function(ev){
        $.post('/connect', $('#connect-form').serialize(), function(data){
            $('.before-submit').hide();
            $('#submit-message').removeClass('hidden');
        });
        ev.preventDefault();
    });
});
