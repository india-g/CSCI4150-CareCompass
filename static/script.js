const maxChatCount = 500;
function deleteTopChat(area) {
    area.removeChild(area.firstElementChild);
}

function addChat(area, text, classes) {
    const p = document.createElement("p");
    p.className = classes;
    p.textContent = text;
    area.appendChild(p);

    while (area.childElementCount > maxChatCount) {
        deleteTopChat(area);
    }
    window.scrollTo({
        top: document.documentElement.scrollHeight,
        behavior: 'smooth'
    });
}

const userClasses = "chat chat_user self-end max-w-[75%] rounded-2xl rounded-br-sm bg-blue-500 px-4 py-2 text-white";
const botClasses = "chat chat_bot self-start max-w-[75%] rounded-2xl rounded-bl-sm bg-gray-200 px-4 py-2 text-gray-900";

const history = [];

document.getElementById("submitButton").addEventListener("click", function(e) {
    e.preventDefault();
    let inputField = e.target.previousElementSibling;
    let userInput = inputField.value.trim();
    if (!userInput) return;

    let chatArea = document.getElementById("responseContainer");
    addChat(chatArea, userInput, userClasses);
    inputField.value = "";

    history.push({ role: "user", text: userInput });

    fetch("/api/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ messages: history })
    }).then(response => {
        if (!response.ok) throw new Error(`Server returned ${response.status}`);
        return response.json();
    }).then(data => {
        history.push({ role: "model", text: data.reply });
        addChat(chatArea, data.reply, botClasses);
    }).catch(err => {
        console.error(err);
        history.pop(); // remove the failed user message so roles keep alternating
        addChat(chatArea, "Sorry, something went wrong. Please try again.", botClasses);
    });
});