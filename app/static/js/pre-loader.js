var loader = document.getElementById("preloader");

window.addEventListener("load",()=>{
    setTimeout(function(){loader.style.opacity=0;}, 1000);
    setTimeout(function(){loader.remove();}, 1500);
    // setTimeout(function(){loader.style.visibility = 'hidden';}, 2000);
})