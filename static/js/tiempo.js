// tiempo.js
let timer;
const logoutTime = 240 * 60 * 1000; //4 HORAS Y SE CUENTA EN MINUTOS

function cerrarSesionPorInactividad() {
  window.location.href = logoutUrl;
}

function resetTimer() {
  clearTimeout(timer);
  timer = setTimeout(cerrarSesionPorInactividad, logoutTime);
}

window.onload = resetTimer;
document.onmousemove = resetTimer;
document.onkeypress = resetTimer;
document.onscroll = resetTimer;