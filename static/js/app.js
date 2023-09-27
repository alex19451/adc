function myConfirm() {
  var result = confirm("Want to do?");

  if (result==true) {
   return true;
  } else {
   return false;
  }
}
function isValidIPv4(addr){
  var regex = /^((25[0-5]|2[0-4][0-9]|[0-1]?[0-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|[0-1]?[0-9]?[0-9])$/;
  return regex.test(addr);
}
