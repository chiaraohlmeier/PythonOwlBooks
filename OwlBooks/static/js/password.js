function togglePassword(inputId, showId, hideId) {
    var pw = document.getElementById(inputId);
    var eyeShow = document.getElementById(showId);
    var eyeHide = document.getElementById(hideId);
    if (pw.type === "password") {
        pw.type = "text";
        eyeShow.style.display = "none";
        eyeHide.style.display = "inline";
    } else {
        pw.type = "password";
        eyeShow.style.display = "inline";
        eyeHide.style.display = "none";
    }
}