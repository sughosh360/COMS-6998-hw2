$(document).ready(function () {
    console.log("Ready!");

 
    function callSearchAPI(query) {
        return sdk.searchGet({ q: query }, {}, {});
    }


    function httpReq(method, url, data, successCB, errorCB) {
        var xhr = new XMLHttpRequest();
       
        xhr.addEventListener('load', function () {
            if (xhr.status == 200) {
                successCB(xhr.response);
               
                document.getElementById("uploadText").innerHTML = "Image Uploaded!!!"
                document.getElementById("uploadText").style.display = "block";
           
            } else {
                errorCB({status: xhr.status, response: xhr.response});
                document.getElementById("uploadText").innerHTML = "Fail to Upload!"
                document.getElementById("uploadText").style.display = "block";
            }
        });

        xhr.open(method, url, true);
        // give access to bucket owner full control
        xhr.setRequestHeader("x-amz-acl", "public-read");
        xhr.send(data);
    }


    function callUploadAPI(image, customLabels) {
        var file = document.getElementById("image-file");
        var fileName = file.name;
        console.log(file.name);
        //http://photo-bucket-6998-hw3-cloud-hw3-test-dev.s3.amazonaws.com/yourKey arn:aws:s3:us-east-1:134260679325:accesspoint/coms-hw2
        httpReq('PUT', 'https://awsphoto-bucket.s3.amazonaws.com/' + fileName.toString(), file, function (response) {
            console.log('Upload Successful', response);
        }, function (error) {
            console.error(error);
        });

        /*var params = {
            'objectKey': document.getElementById("image-file").value,
            'Content-Type': 'image/jpeg',
            'realcontenttype': 'image/jpeg',
            'customlabels': customLabels,
            headers: {
                'Content-Type': 'image/jpeg',
                'realcontenttype': 'image/jpeg',
                'customlabels': customLabels
            },
        };
        console.log(additionalparams);
        return sdk.uploadPut(params, image, additionalparams);*/
    }

    function search() {
        var search_query = $('.search-query').val()
        console.log("Searching for " + search_query);
        $('.search-results').html("");
        callSearchAPI(search_query).then((response) => {
            var image_list = response.data.results;
            console.log(image_list);
           
            var html = '<br>';
            if (image_list.length == 0) {
                html += '<h3>No images found for given tags</h3>'
            } else {
                var i;
                for (i = 0; i < image_list.length; i++) {
                    html += '<img src="' + image_list[i].url + '" witdth="250" height="250" class="thumbnail" /><br><br>'
                }
            }
            console.log(html);
            $(html).appendTo($('.search-results'));
        });
    }

    function upload() {
        var img = document.getElementById("imagebase64").value;
        var comma_index = img.indexOf(",");
        var custom1 = document.getElementById("customLabel1").value;
        var custom2 = document.getElementById("customLabel2").value;
        var custom3 = document.getElementById("customLabel3").value;
        console.log( "custom1="+custom1 )
        console.log( "custom2="+custom2 )
        console.log( "custom3="+custom3 )
        var customLabels = custom1 + ", " + custom2 + ", " + custom3
        console.log( "customLabels="+customLabels )
        var image_str = img.substring(comma_index+1);
        console.log(image_str);
        callUploadAPI(image_str, customLabels);
        $('.upload-message').html("File Uploaded");
    }

    $('.search-button').click(function () {
        search();
    });

    $('.upload-button').click(function () {
        upload();
    });

    $(window).on('keydown', function (e) {
        if (e.which == 13) {
            search();
            return false;
        }
    })

    function readFile() {
 
        if (this.files && this.files[0]) {

            var FR = new FileReader();
            console.log(this.files[0]['name']);
            var filename = this.files[0]['name']
            document.getElementById("image-file").setAttribute("value", filename);
            FR.addEventListener("load", function(e) {
                document.getElementById("img").src = e.target.result;
                document.getElementById("imagebase64").setAttribute("value", e.target.result);
            });

            FR.readAsDataURL( this.files[0] );
        }
       
    }

    document.getElementById("image").addEventListener("change", readFile);

    $(function () {
        // check for support (webkit only)
        if (!('webkitSpeechRecognition' in window)) // todo error
            return;
   
        var input = document.getElementById('input');
        var record = document.getElementById('record');
   
        // setup recognition
        const talkMsg = 'Speak now';
        // seconds to wait for more input after last
        const patience = 5;
        var recognizing = false;
        var timeout;
        var oldPlaceholder = null;
        var recognition = new webkitSpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
   
        function restartTimer() {
            timeout = setTimeout(function () {
                recognition.stop();
            }, patience * 1000);
        }
   
        recognition.onstart = function () {
            oldPlaceholder = input.placeholder;
            input.placeholder = talkMsg;
            recognizing = true;
            restartTimer();
        };
   
        recognition.onend = function () {
            recognizing = false;
            console.log("onend");
            clearTimeout(timeout);
            if (oldPlaceholder !== null)
                input.placeholder = oldPlaceholder;
            search();
        };
   
        recognition.onresult = function (event) {
            clearTimeout(timeout);
   
            // get SpeechRecognitionResultList object
            var resultList = event.results;
            console.log("onresult");
            // go through each SpeechRecognitionResult object in the list
            var finalTranscript = '';
            var interimTranscript = '';
            for (var i = event.resultIndex; i < resultList.length; ++i) {
                var result = resultList[i];
                // get this result's first SpeechRecognitionAlternative object
                var firstAlternative = result[0];
                if (result.isFinal) {
                    finalTranscript = firstAlternative.transcript;
                } else {
                    interimTranscript += firstAlternative.transcript;
                }
            }
            // capitalize transcript if start of new sentence
            var transcript = finalTranscript || interimTranscript;
   
            // append transcript to cached input value
            input.value = transcript;
   
            restartTimer();
        };
   
        record.addEventListener('click', function (event) {
            event.preventDefault();
   
            // stop and exit if already going
            if (recognizing) {
                recognition.stop();
                return;
            }

            // restart recognition
            recognition.start();
        }, false);
    });
});