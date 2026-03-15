document.addEventListener("DOMContentLoaded", function(){

const searchInput = document.getElementById("logSearch")

searchInput.addEventListener("keyup", function(){

let filter = searchInput.value.toLowerCase()

let rows = document.querySelectorAll("tbody tr")

rows.forEach(function(row){

let text = row.innerText.toLowerCase()

if(text.includes(filter)){
row.style.display = ""
}else{
row.style.display = "none"
}

})

})

})