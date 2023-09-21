
async function getNotebook(url) {
    const response = await fetch(url);
    return await response.json();
}

async function renderNotebookAsync(selector, url) {
    var $holder = document.querySelector(selector);

    const ipynb = await getNotebook(url);
    var notebook = nb.parse(ipynb);

    while ($holder.hasChildNodes()) {
        $holder.removeChild($holder.lastChild);
    }
    $holder.appendChild(notebook.render());
    Prism.highlightAll();
}

function renderNotebook(selector, url) {
    renderNotebookAsync(selector, url)
        .then(() => {
            console.log("Loaded notebook.");
        });
}