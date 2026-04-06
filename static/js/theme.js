document.addEventListener("DOMContentLoaded", function(){
    const button = document.getElementById("themeToggle")

    const savedTheme = localStorage.getItem("theme")

    if(savedTheme === "dark"){
    document.body.classList.add("dark-mode")
    button.innerText = "Light Mode"
}

button.addEventListener("click", function(){
    document.body.classList.toggle("dark-mode")

    if(document.body.classList.contains("dark-mode")){

    localStorage.setItem("theme","dark")
    button.innerText = "Light Mode"

    }else{

    localStorage.setItem("theme","light")
    button.innerText = "Dark Mode"

    }

})

})