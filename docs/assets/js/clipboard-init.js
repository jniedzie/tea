// copy-code.js

document.addEventListener('DOMContentLoaded', function () {
  var codeBlocks = document.querySelectorAll('pre code');

  codeBlocks.forEach(function (codeBlock) {
    var copyButton = document.createElement('button');
    copyButton.className = 'copy-button';
    copyButton.textContent = 'Copy';

    copyButton.addEventListener('click', function () {
      var codeToCopy = codeBlock.textContent;
      copyTextToClipboard(codeToCopy);
      copyButton.textContent = 'Copied!';
      setTimeout(function () {
        copyButton.textContent = 'Copy';
      }, 1500);
    });

    // Wrap the code block and button in a container div for positioning
    var container = document.createElement('div');
    container.className = 'code-container';
    container.appendChild(copyButton);
    container.appendChild(codeBlock.cloneNode(true)); // Clone the code block

    codeBlock.parentNode.replaceChild(container, codeBlock);
  });

  function copyTextToClipboard(text) {
    var textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
  }
});
