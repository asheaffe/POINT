

/**
  * @file
  * Uses cystoscape.js to draw a graph based on data provided in a given json file
  *
  */

document.getElementById('myFile').addEventListener('change', loadFile);


function loadFile(event) {
  /**
    * Loads the chosen json file and runs cytoscape based on the formatting within in
    *
    * @param event signifies a button click
    */
  f = event.target.files[0];

  fr = new FileReader();
  fr.addEventListener("load", e => {
    runCytoscape(fr.result);
  });

  fr.readAsText(f);
}

function runCytoscape(data) {
  /**
    * Runs cytoscape.js given the data passed as input
    *
    * @param data signifies the data from the json file that is used for cytoscape formatting
    */
  var cy = window.cy = cytoscape({
    container: document.getElementById('cy'),

    boxSelectionEnabled: false,
    autounselectify: true,

    // styling for cytoscape.js graph
    style: cytoscape.stylesheet()
      .selector('node')
      .css({
        'label': 'data(name)',
        'text-valign': 'center',
        'text-halign': 'center',
        'border-color': 'black',
        'border-width': 8,
        'height': 80,
        'width': 80
      })
      .selector('edge')
      .css({
        'curve-style': 'haystack',
        'width': 6
      })
      .selector(":parent")
      .css({
        'text-valign': 'top',
        'text-halign': 'center',
        'font-size': '100px'
      })
      .selector('node.compound')
      .css({
        'background-opacity': 0,
        'border-width': 0
      })
      .selector("node.container")
      .css({
        'label': 'data(name)',
        'border-width': 10,
        'border-color': 'black',
        'z-index': 1
      })
      .selector("node.s1")
      .css({
        'border-color': '#037324' 
      })
      .selector("node.s2")
      .css({
        'border-color': '#95136a'
      })
      // have the node and edge borders match the above colors
      .selector("node.species1")
      .css({
        'border-color': '#037324',
        'z-index': 7
      })
      .selector("node.species2")
      .css({
        'border-color': '#95136a',
        'z-index': 6
      })
      .selector("edge.species1")
      .css({
        'line-color': '#037324',
        'line-width': 10,
        'z-index': 7
      })
      .selector("edge.species2")
      .css({
        'line-color': '#95136a',
        'line-width': 10,
        'z-index': 6
      })
      .selector("node.query")
      .css({
        'shape': 'triangle'
      })
      .selector('node.ortho_nonexist') //
      .css({
        'background-color': '#9889e2'
      })
      .selector('node.ortho_exists_in') //
      .css({
        'background-color': '#b885d3'
      })
      .selector('node.ortho_exists_out') //
      .css({
        'background-color': '#db8ebb' 
      })
      .selector('node.nonortho') //
      .css({
        'background-color': '#ea979f'
      })
      .selector("node.query")
      .css({
        'shape': 'round-triangle'
      })
      .selector('node.align_nonortho')
      .css({
        'background-color': '#89a1e5'
      })
      .selector('node.nonalign_ortho')
      .css({
        'background-color': '#978ae2' 
      })
      .selector('node.align_ortho')
      .css({
        'background-color': '#b885d3' 
      })
      .selector('edge.align_nonortho')
      .css({
        'line-color': '#89a1e5'
      })
      .selector('edge.nonalign_ortho')
      .css({
        'line-color': '#978ae2' 
      })
      .selector('edge.align_ortho')
      .css({
        'line-color': '#b885d3'
      })
      .selector('edge.align_edge')
      .css({
        'line-color': '#acd5b2'
      })
      .selector('edge.ortho_edge')
      .css({
        'line-color': '#f4c0c5'
      })
      .selector('edge.alignortho_edge')
      .css({
        'line-color': '#f2d79e'
      })
      // do not show alignment species nodes
      .selector('node.alignment')
      .css({
        'display': 'none'
      }),

    elements: JSON.parse(data),

    ready: function () {
      
      cy = this;

      // take nodes in alignment json
      var align_eles = cy.$(function (element) {
        return element.hasClass('align_ortho') || element.hasClass('align_nonortho') || element.hasClass('nonalign_ortho') 
        || element.hasClass('plain_interaction') || element.hasClass('compound');
      });

      var align_layout = align_eles.layout({
        name: 'cose-bilkent',
        fit: true,
        randomize: false,
        quality: 'proof',
        idealEdgeLength: 150,
        gravityCompound: 15,
        nestingFactor: .1,
        gravityRangeCompound: 0.25,
        nodeRepulsion: 3000
      });
      align_layout.run();

      // take ortho/alignment edges
      var type_edges = cy.$(function (element) {
        return element.hasClass('align_edge') || element.hasClass('ortho_edge') || element.hasClass('alignortho_edge');
      });

      var type_layout = type_edges.layout({
        name: 'cose-bilkent',
        randomize: false,
        idealEdgeLength: 5,
        edgeElasticity: .5
      });
      type_layout.run();

      // layout for orthology view

      // used for toggling zoom
      var current_layout = 'main';

      // only the nodes within the container nodes are in grid format
      // unaligned species 1
      var nodes_s1 = cy.$(function (element, i) {
        return element.hasClass('species1') && (element.hasClass('nonortho') || element.hasClass('ortho_nonexist') || element.hasClass('ortho_exists_in') || element.hasClass('ortho_exists_out'));
      });

      // unaligned species 2
      var nodes_s2 = cy.$(function (element, i) {
        return element.hasClass('species2') && (element.hasClass('nonortho') || element.hasClass('ortho_nonexist') || element.hasClass('ortho_exists_in') || element.hasClass('ortho_exists_out'));
      });

      // make hSize and vSize relative to whichever network is larger
      var hSize = Math.ceil(Math.sqrt(Math.max(nodes_s1.size(), nodes_s2.size())));
      var vSize = Math.ceil(nodes_s1.size() / hSize);

      // hDist and vDist use the size of the nodes and the number of
      // rows and columns to calculate distance from the query
      var hDist = -500 - (80 * hSize);    // horizontal distance
      var vDist = -(80 * vSize) * 0.5;    // vertical distance

      // format layout for species 1 nodes
      const layout1 = nodes_s1.layout({
        name: 'concentric',
        nodeDimensionsIncludeLabels: true,
        fit: false,
        padding: 2,
        //animate: true,
        avoidOverlapPadding: 3,
        boundingBox: { x1: hDist, y1: vDist, w: 2, h: 2 },
        sort: function (a, b) {
          return a.classes().toString().localeCompare(b.classes().toString());
        }
      });

      layout1.run();
      nodes_s1.forEach(function (element, i) {
        element.move({ parent: 'species1' });
      });

      // make the horizontal distance between the two networks relative to the first species
      var hDist = 500 + hSize * 80;

      // format layout for species 2 nodes
      const layout2 = nodes_s2.layout({
        name: 'concentric',
        nodeDimensionsIncludeLabels: true,
        padding: 2,
        //animate: true,
        avoidOverlapPadding: 3,
        boundingBox: { x1: hDist, y1: vDist, w: 30, h: 30 },
        sort: function (a, b) {
          return a.classes().toString().localeCompare(b.classes().toString());
        }
      });
      layout2.run();
      nodes_s2.forEach(function (element, i) {
        element.move({ parent: 'species2' });
      });

      cy.fit();

      // orthologous nodes
      var nodes3 = cy.$(function (element, i) {
        return (element.hasClass('ortho_nonexist') || element.hasClass('ortho_exists_in') || element.hasClass('ortho_exists_out'));
      });

      cy.on('click', 'node', function (evt) {
        if (current_layout === 'main') {
          var select = evt.target;

          // holds the parent node for selected node in either view
          window.group = select.data().parent
          console.log(select.outgoers());
          window.selected_network = select.outgoers().union(select.incomers()).union(select);

          // global value so that elements can be restored later
          window.value = cy.remove(cy.elements()
            .difference(select.outgoers()
              .union(select.incomers())));
          cy.add(window.selected_network);
          cy.elements().layout({
            name: 'grid',
            animate: 'true',
            animationDuration: 500
          }).run();
          current_layout = 'zoom';
        }
      });

      // node dropdown menu options
      // options to be assigned to an instance later.. ?
      var options = {
        // List of initial menu items
        menuItems: [
          {
            // protein name(s), does nothing when clicked
            id: 'protein_name',
            content: 'content here',
            tooltipText: 'Protein Name(s)',
            selector: 'node.protein, node.query, node.aligned, node.species1, node.species2'
          },
          {
            // click for ensembl link for first protein
            id: 'ensembl_link1',
            content: "ensembl species 1",
            tooltipText: "Visit Ensembl page",
            selector: "node.protein, node.query, node.aligned, node.species1, node.species2",
            onClickFunction: function (event) {
              if (event.target.data('e_id').startsWith("N/A")) {

              } else {
                window.open("http://www.ensembl.org/id/" + event.target.data("e_id"));
              }
            }
          },
          {
            // click for ensembl link for second protein
            id: 'ensembl_link2',
            content: "ensembl species 2",
            tooltipText: "Visit Ensembl page",
            selector: "node.protein, node.query, node.aligned, node.species1, node.species2",
            onClickFunction: function (event) {
              if (event.target.data("e_id2") === undefined) {

              } else {
                window.open("http://www.ensembl.org/id/" + event.target.data("e_id2"));
              }
            }
          },
          {
            // ncbi link for first protein
            id: "ncbi_link1",
            content: "ncbi species 1",
            tooltipText: "Visit NCBI page",
            selector: "node.position, node.query, node.aligned, node.species1, node.species2",
            onClickFunction: function (event) {
              if (event.target.data("ncbi") === undefined) {

              } else {
                window.open("https://www.ncbi.nlm.nih.gov/gene/" + event.target.data("ncbi"));
              }
            }
          },
          {
            // ncbi link for second protein
            id: "ncbi_link2",
            content: "ncbi species 2",
            tooltipText: "Visit NCBI page",
            selector: "node.position, node.query, node.aligned, node.species1, node.species2",
            onClickFunction: function (event) {
              if (event.target.data("ncbi2") === undefined) {

              } else {
                window.open("https://www.ncbi.nlm.nih.gov/gene/" + event.target.data("ncbi2"))
              }
            }
          },
          {
            // uniprot link for first protein
            id: "uniprot_link1",
            content: "uniprot species 1",
            tooltipText: "Visit Uniprot page",
            selector: "node.position, node.query, node.aligned, node.species1, node.species2",
            onClickFunction: function (event) {
              if (event.target.data("uniprot") === undefined) {

              } else {
                window.open("https://www.uniprot.org/uniprotkb/" + event.target.data("uniprot"));
              }
            }
          },
          {
            // uniprot link for second protein
            id: "uniprot_link2",
            content: "uniprot species 2",
            tooltipText: "Visit Uniprot page",
            selector: "node.position, node.query, node.aligned, node.species1, node.species2",
            onClickFunction: function (event) {
              if (event.target.data("uniprot2") === undefined) {

              } else {
                window.open("https://www.uniprot.org/uniprotkb/" + event.target.data("uniprot2"));
              }
            }
          }
        ]
      };
      // instance of dropdown menu with options as defined above
      var instance = cy.contextMenus(options);

      cy.on("cxttapstart", "node", function (event) {


        // format protein names
        var node_name = event.target.data("name");
        var name_arr = node_name.split(",");

        //console.log(name_arr);

        instance.disableMenuItem("protein_name");
        document.getElementById("protein_name").innerHTML = node_name;

        // ensembl id species 1
        if (event.target.data("e_id") === undefined) {
          instance.hideMenuItem("ensembl_link1");
        } else {
          instance.showMenuItem("ensembl_link1");
          document.getElementById("ensembl_link1").innerHTML = "Ensembl (" + name_arr[0] + ")";
        }

        // ensembl id species 2
        if (event.target.data("e_id2") === undefined) {
          instance.hideMenuItem("ensembl_link2");
          document.getElementById("ensembl_link1").innerHTML = "ensembl";
        } else {
          instance.showMenuItem("ensembl_link2");
          document.getElementById("ensembl_link2").innerHTML = "Ensembl (" + name_arr[1] + ")";
        }

        // ncbi id species 1
        if (event.target.data("ncbi") === undefined) {
          instance.hideMenuItem("ncbi_link1");
        } else {
          instance.showMenuItem("ncbi_link1");
          document.getElementById("ncbi_link1").innerHTML = "NCBI (" + name_arr[0] + ")";
        }

        // ncbi id species 2
        if (event.target.data("ncbi2") === undefined) {
          instance.hideMenuItem("ncbi_link2");
          document.getElementById("ncbi_link1").innerHTML = "ncbi";
        } else {
          instance.showMenuItem("ncbi_link2");
          document.getElementById("ncbi_link2").innerHTML = "NCBI (" + name_arr[1] + ")";
        }

        // uniprot id species 1
        if (event.target.data("uniprot") === undefined) {
          instance.hideMenuItem("uniprot_link1");
        } else {
          instance.showMenuItem("uniprot_link1");
          document.getElementById("uniprot_link1").innerHTML = "Uniprot (" + name_arr[0] + ")";
        }

        // uniprot id species 2
        if (event.target.data("uniprot2") === undefined) {
          instance.hideMenuItem("uniprot_link2");
          document.getElementById("uniprot_link1").innerHTML = "uniprot";
        } else {
          instance.showMenuItem("uniprot_link2");
          document.getElementById("uniprot_link2").innerHTML = "Uniprot (" + name_arr[1] + ")";
        }

      });

      // implementing jscolor to change the color scheme of network
      updateSpecies1Color = function (jscolor) {
        cy.startBatch();
        // change the color of the species 1 nodes
        cy.style().selector('node.species1').css({
          'background-color': jscolor.toString()
        }).update();

        // change the color of the species 1 edges
        cy.style().selector('edge.species1').css({
          'line-color': jscolor.toString()
        }).update();

        var temp_jscolor = 'color:' + jscolor.toString();

        // change the color of the text in the legend
        document.getElementById('s1').style = temp_jscolor;

        cy.endBatch();
      };

      // implement jscolor to change the legend color for species 2
      updateSpecies2Color = function (jscolor) {
        cy.startBatch();

        // change color of species 2 nodes
        cy.style().selector('node.species2').css({
          'background-color': jscolor.toString()
        }).update();

        // change the color of species 2 edges
        cy.style().selector('edge.species2').css({
          'line-color': jscolor.toString()
        }).update();

        var temp_jscolor = 'color: ' + jscolor.toString();

        // change the color within the legend text
        document.getElementById('s2').style = temp_jscolor
        cy.endBatch();
      };

      // implement jscolor to change the legend color for the aligned proteins
      updateAlignedColor = function (jscolor) {
        cy.startBatch();

        // change color of aligned nodes
        cy.style().selector('node.nOrtho').css({
          'background-color': jscolor.toString()
        }).update();

        // change the color of aligned edges
        cy.style().selector('edge.aligned').css({
          'line-color': jscolor.toString()
        }).update();

        var temp_jscolor = 'color: ' + jscolor.toString();

        // change the color within the legend text
        document.getElementById('aligned').style = temp_jscolor;

        cy.endBatch();
      };

      //      // id for container species1
      //      var cont_node1 = cy.$(function(element, i){
      //        return element.hasClass("container") && element.hasClass("s1");
      //      })

      var json = JSON.parse(data);
      species1_id = json[0]["data"]["name"];    // holds species1 name
      species2_id = json[1]["data"]["name"];    // holds species2 name

      //      id for container species2
      //      var cont_node2 = cy.$(function(element, i) {
      //        return element.hasClass("container") && element.hasClass("s2");
      //      })

      // aligned edge composition
      var align_e = cy.$(function (element, i) {
        return element.hasClass("aligned") && element.hasClass("edge");
      })

      // grab all of the edges
      var all_edges = cy.$(function (element, i) {
        return element.hasClass("edge");
      })

      // total orthologous nodes
      ortho_n = cy.$(function (element, i) {
        return element.hasClass('ortho') && element.hasClass('protein');
      })

      // aligned edges between orthologous nodes.
      ortho_e = nodes3.connectedEdges().filter('.aligned');

      // array of stats to be passed to the windows
      // TODO: Change the stats for the ortho view - most of them are dependent on alignment
      var stats = [nodes3.size(), ortho_n.size(), nodes_s1.size(), nodes_s2.size(), align_e.size(), ortho_e.size(), all_edges.size()];

      // collect all of the proteins in the network
      var all_nodes = cy.$(function (element, i) {
        return element.hasClass("protein");
      });

      buildTable(all_nodes);

      // buttons open corresponding windows
      openMainItem("#b1", "#button1", 'fit-content', 0, stats, species1_id, species2_id, cy);
      //openMainItem("#b2", "#button2", 300, 20, stats, species1_id, species2_id);
      openMainItem("#b3", "#button3", 'fit-content', 500, stats, species1_id, species2_id, cy);
      openMainItem("#b2_colors", "#color_pick", 'fit-content', 500, stats, species1_id, species2_id, cy);
      openMainItem("#b2_data", "#data_ctrl", 'fit-content', 500, stats, species1_id, species2_id, cy);

      // create a reset button that will appear below it
      var resetView = document.createElement("BUTTON");
      resetView.setAttribute('id', 'resetView');
      var buttonText = document.createTextNode("Reset");
      resetView.appendChild(buttonText);
      document.getElementById('cy').appendChild(resetView);

      // function for reset button click
      resetView.onclick = function () {

        // global var with removed elements
        window.value.restore();
        window.selected_network.restore();
        layout1.run();
        nodes_s1.forEach(function (element, i) {
          element.move({ parent: 'species1' });
        });
        layout2.run();
        nodes_s2.forEach(function (element, i) {
          element.move({ parent: 'species2' });
        });
        align_layout.run();
        //alert(window.group);
        type_layout.run();
        cy.elements().forEach(function (element, i) {
          var node_parent = element.data().parent;
          
          if (node_parent !== undefined) {
            element.move({ parent: node_parent });
          } else {
            console.log(element.data().parent);
          };
        });
        cy.animate({
          fit: {
            eles: cy.elements()
          }
        },
          {
            duration: 500
          });
        current_layout = 'main';
      }
    } // ready

  }); // cy init

  // panzoom slider with defaults
  cy.panzoom({
    animateOnFit: function () {
      return true;
    }
  });
}

// plugin initialization

// dropdown menu plugin


/**
  * Copies the text that within the data sidebar
  *
  */
function copyText() {
  var txt = document.getElementById("data_tbl").innerHTML;

  // edit the raw HTML string
  txt = txt.replace(/<tr>/g, '');
  txt = txt.replace(/<th>/g, '');
  txt = txt.replace(new RegExp("</th>", 'g'), '\t');
  txt = txt.replace(new RegExp("</tr>", 'g'), '\n');
  txt = txt.replace(/<td>/g, '');
  txt = txt.replace(new RegExp("</td>", 'g'), '\t');

  navigator.clipboard.writeText(txt);

  alert("Copied: " + txt);
}

// function for making a data table
function buildTable(proteins) {
  // building the sidebar data table
  // developed from demo on delftstack.com
  var table = document.getElementById('data_tbl');

  // create a table row for the header
  var header_row = document.createElement('tr');

  // create rows for each data section
  var heading1 = document.createElement('th');
  heading1.innerHTML = "Protein";
  var heading2 = document.createElement('th');
  heading2.innerHTML = "Species1";
  var heading3 = document.createElement('th');
  heading3.innerHTML = "Species2";
  var heading4 = document.createElement('th');
  heading4.innerHTML = "Aligned";
  var heading5 = document.createElement('th');
  heading5.innerHTML = "Orthologous";

  // append the heading to the header row
  header_row.appendChild(heading1);
  header_row.appendChild(heading2);
  header_row.appendChild(heading3);
  header_row.appendChild(heading4);
  header_row.appendChild(heading5);

  // append the row to the table
  table.appendChild(header_row);

  // loop through all of the nodes
  for (let i = 0; i < proteins.size(); i++) {
    var current = proteins[i].data("name");

    // make a 2D array of data
    // the purpose of having this overarching array is to alphabetize the data
    var data_arr = [];

    // temporary array that will hold both the name array and the class array
    var temp_arr = [];

    var name_arr = [];
    // separate proteins if two are present
    // if (current.includes(",")) {
    //   name_arr = current.split(",");
    // } else {
    //   name_arr.push(current);
    // }

    // add the array of names to the 2D data array
    temp_arr.push(name_arr);

    // class array will hold boolean values indicating which type of node is present
    var class_arr = [];

    class_arr.push(proteins[i].hasClass("species1"));
    class_arr.push(proteins[i].hasClass("species2"));
    class_arr.push(proteins[i].hasClass("nOrtho"));
    class_arr.push(proteins[i].hasClass("ortho"));

    temp_arr.push(class_arr);

    data_arr.push(temp_arr);

    // loop through the temp array and make a row for each element
    for (let k = 0; k < name_arr.length; k++) {
      // create a row in the table
      var prot_row = document.createElement('tr');

      // data that will hold the protein name
      var name = document.createElement('td');
      name.innerHTML = name_arr[k];

      // data that will hold boolean value for species 1
      var s1 = document.createElement('td');
      s1.innerHTML = class_arr[0];

      // data that will hold boolean value for species 2
      var s2 = document.createElement('td');
      s2.innerHTML = class_arr[1];

      // boolean value for aligned non-orthologous proteins
      var al = document.createElement('td');
      al.innerHTML = class_arr[2];

      // boolean value for aligned orthologous proteins
      var ort = document.createElement('td');
      ort.innerHTML = class_arr[3];

      // append each piece of data to the current row in order
      prot_row.appendChild(name);
      prot_row.appendChild(s1);
      prot_row.appendChild(s2);
      prot_row.appendChild(al);
      prot_row.appendChild(ort);

      table.appendChild(prot_row);
    }

  }
}

// dropdown menu for header tabs
// takes the id of the dropdown div as param
function ctrlDrop(el) {
  var temp = document.getElementById(el).style.display.toString();

  // check if the dropdown is toggled on
  if (temp === "block") {
    document.getElementById(el).style.display = "none";
  } else {
    document.getElementById(el).style.display = 'block';
  };
}

// code taken from jqueryui.com
// makes elements in div window to be draggable
function dragItem(win) {
  /**
    * Pass the id for a given window by parameter so that it will be made draggable
    * using jquery
    *
    * @param win indicates the html div id for a given window
    */
  $(win)
    .draggable({
      scroll: false
    });
}

// makes elements in div window to be resizable
function resizeItem(win) {
  /**
    * Uses div id for a given window to make that div resizeable
    *
    * @param win indicates the html div id for a given window
    */
  $(win).resizable().css({ 'overflow': 'hidden' });
}

// opens an item that doesnt include any data that would be included in the main items
function openColorPick(button, win, s1_name, s2_name) {
  /**
    * Makes the color picker window open when a button is clicked
    *
    * @param button is the div id for the link to be clicked that will open the window
    * @param win is the html div id that will be opened when the button is clicked
    * @param s1_name is the scientific name of species 1
    * @param s2_name is the scientific name of species 2
    */
  $(button).click(function () {
    $(win).toggle();
    //resizeItem(win);
  });

  // check if the color picker window is open
  if (win === "#color_pick") {
    document.getElementById("species1_text").innerHTML = s1_name + ": ";
    document.getElementById("species2_text").innerHTML = s2_name + ": ";
  }
}


// opens the div and gives it the ability to drag and resize
// param: given button, window to be opened, y-location, x-location, list of stats, names for each species
function openMainItem(button, win, top, left, stat_list, s1_name, s2_name, cy) {
  /**
    * opens the div and gives it the ability to drag and resize
    *
    * @param button name of button that will be clicked to open window
    * @param win name of the window to be opened
    * @param top y-coordinate where the top of the window will be placed on the screen
    * @param left x-coordinate where the left of the window will be placed on the screen
    * @param stat_list list of stats to be included in the stats window (more info below)
    * @param s1_name name of species 1
    * @param s2_name name of species 2
    * @param cy cytoscape object
    */
  // stat list index definitions:
  // 0: number of orthologous proteins
  // 1: number of unaligned species1
  // 2: number of unaligned species2
  // 3: number of aligned edges
  // 4: number of interologs
  // 5: count of all edges

  // check if the current button is the stats button
  if (win === "#button1") {
    // calculate percentage of orthologous aligned nodes to non-ortho aligned nodes
    var per_ortho = Math.round((stat_list[0] / (stat_list[1] + stat_list[0])) * 1000) / 10;
    //console.log(stat_list[0]/(stat_list[1] + stat_list[0])); //// making sure that the output value is correct

    var output = per_ortho + "% (" + stat_list[0] + "/" + (stat_list[1] + stat_list[0]) + ") of aligned proteins are orthologous";

    document.getElementById("b1text1").innerHTML = output;

    // number of aligned species 1 proteins
    // calculate total species 1
    var s1_total = stat_list[0] + stat_list[1] + stat_list[2];

    // calc the number of aligned proteins over total
    var s1_align = (stat_list[0] + stat_list[1]) / s1_total;

    document.getElementById("b1text2").innerHTML = Math.round(s1_align * 1000) / 10 + "% (" + (stat_list[0] + stat_list[1]) + "/" + s1_total + ") of " + s1_name + " proteins are aligned";

    // number of aligned species 2 proteins
    // calculate total species 2
    var s2_total = stat_list[0] + stat_list[1] + stat_list[3];

    // calculate the number of aligned proteins over the total
    var s2_align = (stat_list[0] + stat_list[1]) / s2_total;

    document.getElementById("b1text3").innerHTML = Math.round(s2_align * 1000) / 10 + "% (" + (stat_list[0] + stat_list[1]) + "/" + s2_total + ") of " + s2_name + " proteins are aligned";

    // number of aligned edges that are orthologous
    var intero_al = (stat_list[5] / stat_list[4]);

    document.getElementById("b1text4").innerHTML = Math.round(intero_al * 1000) / 10 + "% (" + stat_list[5] + "/" + stat_list[4] + ") aligned edges are interologs";

    // number of orthologous edges out of all edges
    var intero_total = (stat_list[5] / stat_list[6]);

    document.getElementById("b1text5").innerHTML = Math.round(intero_total * 1000) / 10 + "% (" + stat_list[5] + "/" + stat_list[6] + ") of all edges are interologs";
  };

  // check if the current button is the legend button
  if (win === "#button3") {
    // change the text within the legend window for species1 and species2
    document.getElementById("s1").innerHTML = s1_name;
    document.getElementById("s2").innerHTML = s2_name;

    // get the color property for the species 1 nodes
    var species1_eles = cy.$(function (element) {
      return element.hasClass('species1');
    });

    // get the color property for the species 2 nodes
    var species2_eles = cy.$(function (element) {
      return element.hasClass('species2');
    });

    var ortho_nonexist_eles = cy.$(function (element) {
      return element.hasClass('ortho_nonexist');
    });

    var ortho_exists_in_eles = cy.$(function (element) {
      return element.hasClass('ortho_exists_in');
    });

    var ortho_exists_out_eles = cy.$(function (element) {
      return element.hasClass('ortho_exists_out');
    });

    var nonortho_eles = cy.$(function (element) {
      return element.hasClass('nonortho');
    });

    var ortho_nonexist_eles = cy.$(function (element) {
      return element.hasClass('ortho_nonexist');
    });

    var align_nonortho_eles = cy.$(function (element) {
      return element.hasClass('align_nonortho');
    });

    var nonalign_ortho_eles = cy.$(function (element) {
      return element.hasClass('nonalign_ortho');
    });

    var align_ortho_eles = cy.$(function (element) {
      return element.hasClass('align_ortho');
    });

    // take the species colors
    var species1_color = species1_eles.style('border-color');
    var species2_color = species2_eles.style('border-color');

    var ortho_nonexist_color = ortho_nonexist_eles.style('background-color');
    var ortho_exists_in_color = ortho_exists_in_eles.style('background-color');
    var ortho_exists_out_color = ortho_exists_out_eles.style('background-color');
    var nonortho_color = nonortho_eles.style('background-color');
    var align_nonortho_color = align_nonortho_eles.style('background-color');
    var nonalign_ortho_color = nonalign_ortho_eles.style('background-color');
    var align_ortho_color = align_ortho_eles.style('background-color');

    // change the color of the species 1 and 2 legend text
    document.getElementById("s1").style.color = species1_color;
    document.getElementById("s2").style.color = species2_color;   
    
    document.getElementById("ortho_nonexist").style.color = ortho_nonexist_color;
    document.getElementById("ortho_exists_in").style.color = ortho_exists_in_color;
    document.getElementById("ortho_exists_out").style.color = ortho_exists_out_color;
    document.getElementById("nonortho").style.color = nonortho_color;
    document.getElementById("align_nonortho").style.color = align_nonortho_color;
    document.getElementById("nonalign_ortho").style.color = nonalign_ortho_color;
    document.getElementById("align_ortho").style.color = align_ortho_color;

  }

  $(button).click(function () {
    $(win).toggle();

    // controls when to open and close the sidebar
    if ($("#button1").css("display") === 'block' || $('#button3').css("display") === 'block' || $("#color_pick").css("display") === 'block') {
      if ($('#color-pick').css("display") === 'block') {
        // opens the color picker option in controls
        openColorPick("#b2_colors", "#color_pick", species1_id, species2_id);
      }
      else if (button === '#b2_data') {
        $("#data_ctrl").toggle();
      }
      document.getElementById('cy').style = "left:25%;";
    }
    else if ($("#button1").css("display") === "none" && $('#button3').css("display") === 'none' && $("#color_pick").css("display") === 'none') {
      document.getElementById('cy').style = "left:5%;";
    }
  });

  $(win).css({ 'top': top, 'left': left, 'height': 'fit-content', 'overflow': 'hidden' });

}

// stellarnav import js
jQuery(document).ready(function ($) {
  jQuery('.stellarnav').stellarNav({
    theme: 'dark',
    position: 'static',
    showArrows: true,
    sticky: false,
    closeLabel: 'Close',
    scrollbarFix: false,
    menuLabel: 'Menu'
  });
});


/*
let test = cy.$('#n0');
let neighborhood = test.neighborhood().filter('node');
for (let neighbor of neighborhood) {
  console.log(neighbor.data('id'));
} */