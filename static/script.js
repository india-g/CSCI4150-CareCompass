document.getElementById("submitButton").addEventListener("click", function(e) {
    e.preventDefault();
    let userInput = e.target.previousElementSibling.value;
    console.log(userInput);

    fetch("/api/test", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ text: userInput })
    }).then(response => response.json()).then(data => {
        console.log(data);
    });
});