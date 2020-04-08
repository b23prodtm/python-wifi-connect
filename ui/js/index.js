$(function(){
    var devices = undefined;

    function hideFormFields() {
        // start off with all fields hidden
        $('#service-group').addClass('hidden');
        $('#protoport-group').addClass('hidden');
    }

    function status(data){
        if(data.length !== 0){
            $('#status').val(data);
        } else {
            $('.reg-row').hide(); // display device information
	      }
    }

    $('#bt_addr-select').change(hideFormFields);

    $.get("/pincode", function(data){
        if(data.length !== 0){
            $('#pincode').val(data);
        } else {
            $('.reg-row').hide(); // no reg code, so hide that part of the UI
	}
    });

    $.get("/status", status);

    $.get("/devices", function(data){
        if(data.length === 0){
            $('.before-submit').hide();
            $('#no-devices-message').removeClass('hidden');
        } else {
            devices = JSON.parse(data);
            $.each(devices, function(index, name){
                $('#bt_addr-select').append(
                    $('<option>')
                        .text(name)
                        .attr('val', index)
                        //.attr('data-security', val.security.toUpperCase())
                );
            });

            jQuery.proxy(hideFormFields, $('#bt_addr-select'))();
        }
    });

    $('#connect-form').submit(function(ev){
        $.post('/connect', $('#connect-form').serialize(), function(data){
            $('.before-submit').hide();
            $('#submit-message').removeClass('hidden');
            status(data);
        });
        ev.preventDefault();
    });
});
