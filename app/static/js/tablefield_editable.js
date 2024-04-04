var btnEdits = document.querySelectorAll('#edit');
    var btnCancels = document.querySelectorAll('#cancel');
    var btnUpdate = document.querySelectorAll('#update');
    var btnDelete = document.querySelectorAll('#delete');

    btnEdits.forEach((btnEdit)=>{
        btnEdit.addEventListener('click',editable);
    });
    
    btnCancels.forEach((btnCancel)=>{
        btnCancel.addEventListener('click',editable)
    });

    function editable(event) {
        var row = event.target.closest('tr');
        var inputElements = row.querySelectorAll('input:not([type=radio])');
        var spanElements = row.querySelectorAll('span');

        inputElements.forEach((inputElement) => {
            inputElement.style.display = (inputElement.style.display === 'none') ? 'inline-block' : 'none';
        });
        spanElements.forEach((spanElement) => {
            spanElement.style.display = (spanElement.style.display === 'none') ? 'inline-block' : 'none';
        });
            // Toggle the display of the edit, update, and cancel links
        row.querySelector('#edit').style.display = (row.querySelector('#edit').style.display === 'none') ? 'inline-block' : 'none';
        row.querySelector('#update').style.display = (row.querySelector('#update').style.display === 'none') ? 'inline-block' : 'none';
        row.querySelector('#cancel').style.display = (row.querySelector('#cancel').style.display === 'none') ? 'inline-block' : 'none';
        row.querySelector('#delete').style.display = (row.querySelector('#delete').style.display === 'none') ? 'inline-block' : 'none';
    }

    function changeFormAction(button){
        var closesttd = button.parentElement;
        var form = closesttd.parentElement;
        if(form){
            var barcodeInput = form.querySelector('#barcode');
            //
            console.log(barcodeInput)
        }else{
            console.log('Form not found')
        }
    }