window.ml = cloudinary.createMediaLibrary({
    cloud_name: 'papish',
    api_key: '795453237454584',
    username: 'yuval.papish@cloudinary.com',
    timestamp: 1518601863,
    button_class: 'myBtn',
    signature: '4b7694a533eb9079e098e2a77891fb9747d8f5b38ca510bd60745e92efbdca19', // SHA256(cloud_name=papish&timestamp=1518601863&username=yuval.papish@cloudinary.coma795453237454584"
    button_caption: 'Select Image or Video',
}, {
    insertHandler: function (data) {
        data.assets.forEach(asset => {
            console.log('Inserted asset:',
                JSON.stringify(asset, null, 2));
        });
    }
},
document.getElementById('myBtn')
);
