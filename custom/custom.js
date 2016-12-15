// Custom Javascript for the notebooks

// Customization 1 - change the autosave interval to 10 seconds
//
// Source:
// https://www.webucator.com/blog/2016/03/change-default-autosave-interval-in-ipython-notebook/

define([
    'base/js/namespace',
    'base/js/events'
    ],
    function(IPython, events) {
        events.on("notebook_loaded.Notebook",
            function () {
                    IPython.notebook.set_autosave_interval(10000); //in milliseconds
                }
            );
        //may include additional events.on() statements
    }
);
