import './style.css';
import {Feature, Map, View} from 'ol';
import OSM from 'ol/source/OSM';
import Point from 'ol/geom/Point.js';
import VectorSource from 'ol/source/Vector';
import VectorLayer from 'ol/layer/Vector';
import GeoJSON from 'ol/format/GeoJSON.js';
import Overlay from 'ol/Overlay';
import LayerGroup from 'ol/layer/Group';
import Style from 'ol/style/Style';
import Stroke from 'ol/style/Stroke';
import Fill from 'ol/style/Fill.js';
import GeoTIFF from 'ol/source/GeoTIFF.js';
import TileLayer from 'ol/layer/WebGLTile.js';


window.onload = init;
function init(){


const map = new Map({
  target: 'map',
   view: new View({
    center: [13.0214403, 47.8208613],
    projection: "EPSG:4326",
    zoom: 13,
    maxZoom: 16,
    minZoom:12
  })
});

var openStreetMapStandard = new TileLayer({
  source: new OSM(),
  visible: true,
  title: 'OSMStandard'
})

var openStreetMapTopo = new TileLayer({
  source: new OSM({
    url: 'https://{a-c}.tile.opentopomap.org/{z}/{x}/{y}.png'
  }),
  visible: false,
  title: 'OSMTopo'

})

var source = new GeoTIFF({
  sources:[
    {
      url:'https://ecostress.s3.eu-central-1.amazonaws.com/summer/Median_Salzburg_Summer_18_Masked_cog.tif',
      bands:[1],
      min: 4,
      max: 40,
    },
  ],
});

var summer = new TileLayer({
  title:"summer",
  source:source
})


//Layer Group

var baseLayerGroup = new LayerGroup({
  layers: [openStreetMapStandard,openStreetMapTopo,summer]
})

map.addLayer(baseLayerGroup)


//Layer Switcher Logic for Basemaps

var baseLayerElements = document.querySelectorAll(".sidebar > input[type = radio]");
for(let baseLayerElement of baseLayerElements){
  baseLayerElement.addEventListener('change', function(){
    let baseLayerElementValue = (this.value);
    baseLayerGroup.getLayers().forEach(function(element,index,array){
      let baseLayerTitle = (element.get('title'));
      element.setVisible(baseLayerTitle === baseLayerElementValue);
    })
  })
}

var gradColors = [  [0, 'rgb(13,8,136, 0.7)'],
  [16, 'rgb(71,3,160,0.7)'],
  [25, 'rgb(116,1,169,0.7)'],
  [27, 'rgb(156,23,159,0.7)'],
  [29, 'rgb(190,55,134, 0.7)'],
  [31, 'rgb(216,87,108, 0.7)'],
  [33, 'rgb(238,121,83, 0.7)'],
  [35, 'rgb(251,159,59, 0.7)'],
  [37, 'rgb(254,202,38, 0.7)'],
  [39, 'rgb(241,250,34, 0.7)']
  
];

var graduatedStyle = function graduatedColor(feature) {
  var mean = feature.get('s_mean_2018');
  var color = gradColors[0][1];
  for (var i = 0; i < gradColors.length; i++) {
    if (mean > gradColors[i][0]) {
      color = gradColors[i][1];
    }
  }
  return new Style({
    fill: new Fill({
      color: color,
      
    }),
    stroke: new Stroke({
      color: 'rgba(30, 30, 30, 0.2)',
      width: 2,
    }),
  });
}

var hexagons_June = new VectorLayer({
  source: new VectorSource({
    url: "./data/Hexagons_20000.geojson",
    format: new GeoJSON()
  }),
  visible: true,
  title: "Temperature Anomalies",
  style: graduatedStyle
});


map.addLayer(hexagons_June);

// Vector Feature Popup Logic
var overlayContainerElement = document.querySelector(".overlay-container");
var overlayLayer = new Overlay({
  element: overlayContainerElement
})
map.addOverlay(overlayLayer);
var overlayFeatureGrid = document.getElementById("feature-grid")
var overlayFeatureMean = document.getElementById("feature-mean")

map.on('click', function(e){
  overlayLayer.setPosition(undefined)
  map.forEachFeatureAtPixel(e.pixel, function(feature,layer){
    const layerName = layer.get('title');
    const lastFourChars = layerName.substr(-4);
    let clickedCoordinate = e.coordinate;
    let clickedFeatureGrid = "Mean LST (°C)" + lastFourChars;
    let clickedFeatureMean= feature.get("s_mean_2018");
    overlayLayer.setPosition(clickedCoordinate);
    overlayFeatureGrid.innerHTML = clickedFeatureGrid;
    overlayFeatureMean.innerHTML = clickedFeatureMean;
  },
  {
    layerFilter: function(layerCandidate){
      const title = layerCandidate.get('title');
      return title && title.startsWith('Temperature');
    }
  })
})

// create styles for selected and highlighted features

var highlightStyle = function(feature) {
  var mean = feature.get('s_mean_2018');
  var color = gradColors[0][1];
  for (var i = 0; i < gradColors.length; i++) {
    if (mean > gradColors[i][0]) {
      color = gradColors[i][1];
    }
  }
  return new Style({
    fill: new Fill({
      color: color
    }),
    stroke: new Stroke({
      color: 'rgba(30, 30, 30, 0.9)',
      width: 4,
    }),
  });
};


// current highlighted feature
var highlightedFeature = null;

// pointermove event
map.on('pointermove', function(e) {
  var pixel = map.getEventPixel(e.originalEvent);
  var hit = map.hasFeatureAtPixel(pixel);

  if (hit) {
    map.getTargetElement().style.cursor = 'pointer';

    var feature = map.forEachFeatureAtPixel(pixel, function(feature, layer) {
      if (layer.get('title') === 'Temperature Anomalies') {
        return feature;
      }
    });

    if (feature !== highlightedFeature) {
      if (highlightedFeature) {
        highlightedFeature.setStyle(highlightedFeature.getStyle()[0]); // set original style
      }
      if (feature) {
        feature.setStyle(highlightStyle);
      }
      highlightedFeature = feature;
    }
  } else {
    map.getTargetElement().style.cursor = '';
    if (highlightedFeature) {
      highlightedFeature.setStyle(highlightedFeature.getStyle()[0]); // set original style
      highlightedFeature = null;
    }
  }
  
});



}

