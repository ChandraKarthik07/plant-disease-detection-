var MAX_WIDTH = 400;
var MAX_HEIGHT = 400;

// Create a new DataTransfer object to store resized images
var container = new DataTransfer();

var resizeAndBlob = function() {
    var images = document.getElementById("files").files;
    
    var dataURLToBlob = function(dataURL) {
        var BASE64_MARKER = ';base64,';
        var parts = dataURL.split(BASE64_MARKER);
        var contentType = parts[0].split(':')[1];
        var sliceSize = 1024;
        var byteCharacters = atob(parts[1]);
        var bytesLength = byteCharacters.length;
        var slicesCount = Math.ceil(bytesLength / sliceSize);
        var byteArrays = new Array(slicesCount);

        for (var sliceIndex = 0; sliceIndex < slicesCount; ++sliceIndex) {
            var begin = sliceIndex * sliceSize;
            var end = Math.min(begin + sliceSize, bytesLength);

            var bytes = new Array(end - begin);
            for (var offset = begin, i = 0; offset < end; ++i, ++offset) {
                bytes[i] = byteCharacters[offset].charCodeAt(0);
            }
            byteArrays[sliceIndex] = new Uint8Array(bytes);
        }
        return new Blob(byteArrays, { type: contentType });
    }

    var resizeImage = function(image) {

        if (window.File && window.FileReader && window.FileList && window.Blob) {
            var image_name = image.name;
            var reader = new FileReader();
            // Set the image once loaded into file reader
            reader.onload = function(e) {

                var img = document.createElement("img");
                img.onload = function() {
                    var canvas = document.createElement("canvas");
                    var width = img.width;
                    var height = img.height;

                    // Finding proper image width and size
                    if (width > height) {
                        if (width > MAX_WIDTH) {
                            height *= MAX_WIDTH / width;
                            width = MAX_WIDTH;
                        }
                    }
                    else {
                        if (height > MAX_HEIGHT) {
                            width *= MAX_HEIGHT / height;
                            height = MAX_HEIGHT;
                        }
                    }

                    // Set the canvas width & height and then resize it
                    canvas.width = width;
                    canvas.height = height;
                    var ctx = canvas.getContext("2d");
                    ctx.drawImage(img, 0, 0, width, height);

                    // Create base64 string from canvas
                    var dataUrl = canvas.toDataURL(image.type);
                    // Create a blob form base64 string
                    var blobImage = dataURLToBlob(dataUrl);
                    // Create a file object from blob
                    var file = new File([blobImage], image.name, {type:blobImage.type, lastModified:image.lastModified, lastModifiedDate:image.lastModifiedDate});
                    // Add the file object to container
                    container.items.add(file);
                    // Replace hidden file input every time this function gets called so it get updated to latest container
                    document.getElementById('hiddenfiles').files = container.files;
                    // Image preview code
                    document.getElementById('image_preview').innerHTML += '<div class="card custom-bg-color card-custom-preview mx-2 mb-3"><img src="' + dataUrl + '" class="card-img-top" alt="Crop Image" style="padding-top: 12px; max-height:150px; object-fit: cover;"><div class="card-body"><p class="card-text"><strong>Filename:</strong> ' + image_name + '</p></div></div>';
                }
                img.src = e.target.result;
            }
            reader.readAsDataURL(image);
        }
        else {
            alert('The File APIs are not fully supported in this browser.');
        }
    }

    // Call resize function for all images
    Array.prototype.forEach.call(images, resizeImage);
}

var validate_and_preview = function() {
    // Clean the old Image preview
    if (document.getElementById('image_preview').innerHTML !== "") {
        document.getElementById('image_preview').innerHTML = "";
    }

    // Clean old alert
    document.getElementById('alert').removeAttribute('style');
    document.getElementById('alert').innerHTML = '';

    var images = document.getElementById("files").files;
    var total_files = images.length;

    // Check the file size
    var total_size = 0
    for (var i = 0; i < total_files; i++) {
        var fsize = images.item(i).size; // file size in bytes
        var fsize_mb = fsize / (1024 * 1024); // file size in MB
        total_size += fsize_mb
    }
    // Show alert message for file size greater than 50 MB
    if (total_size >= 50) {
        document.getElementById('alert').setAttribute('style', 'padding-top: 64px;');
        document.getElementById('alert').innerHTML = '<p class="mb-0 mt-3">You uploaded files larger than 50 MB. The Total Maximum file size should be 50 MB.</p>';
        document.getElementById('files').value = "";
        return;
    }

    // Check the file type
    var flag = 0;
    for (var i = 0; i < total_files; i++) {
        var filename = images[i].name;
        var file_list = filename.split(".");
        var file_ext = file_list[file_list.length - 1].toUpperCase();
        var ext = ['JPG', 'JPEG', 'PNG'];
        if (!ext.includes(file_ext)) {
            flag += 1;
            break;
        }
    }
    // Show the alert message for file type other than PNG/JPEG/JPG
    if (flag > 0) {
        document.getElementById('alert').setAttribute('style', 'padding-top: 64px;');
        document.getElementById('alert').innerHTML = '<p class="mb-0 mt-3">You uploaded files other than PNG or JPG/JPEG. We currently supports PNG or JPG/JPEG Image Files Only.</p>';
        document.getElementById('files').value = "";
        flag = 0;
        return;
    }

    document.getElementById('image_preview').innerHTML += '<h4 class="pb-3">Image Preview:</h4>'

    // Resize, convert to blob and add images to hidden file input
    resizeAndBlob();
}

var submit_form = function() {
    if (document.getElementById("hiddenfiles").value === "") {
        document.getElementById('alert').setAttribute('style', 'padding-top: 64px;');
        document.getElementById('alert').innerHTML = '<p class="mb-0 mt-3">Please, select some Images!</p>';
        return false;
    }
    return true;
}

document.getElementById("files").addEventListener("change", validate_and_preview);