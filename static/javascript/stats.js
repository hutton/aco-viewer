/**
 * Created by simonhutton on 03/09/2014.
 */

window.StatsView = Backbone.View.extend({
    initialize: function () {
        this.render();
    },

    template: _.template($('#stats-view-template').html()),

    render: function(){
        this.$el.html(this.template(this.model));

        this.chartEl = this.$el.find('.download-type-chart');

        var ctx = this.chartEl.get(0).getContext("2d");

        var data = {
            labels: ['csv', 'xlsx', 'html', 'xml', 'pdf', 'json', 'txt', 'tsv'],
            datasets: [
            {
                label: "My First dataset",
                fillColor: "rgba(151,187,205,0.2)",
                strokeColor: "rgba(151,187,205,1)",
                pointColor: "rgba(151,187,205,1)",
                pointStrokeColor: "#fff",
                pointHighlightFill: "#fff",
                pointHighlightStroke: "rgba(151,187,205,1)",
                data: this.model.fileTypeFrequencies
            }
        ]};

        new Chart(ctx).Bar(data);

        return this;
    },

    className: 'stat-section'
});

window.TrendView = Backbone.View.extend({
    initialize: function () {
        this.render();
    },

    template: _.template($('#trend-view-template').html()),

    render: function(){
        this.$el.html(this.template(this.model));

        this.chartEl = this.$el.find('.download-type-chart');

        var ctx = this.chartEl.get(0).getContext("2d");

        var data = {
            labels: this.model.labels,
            datasets: [
            {
                label: "Uploads",
                fillColor: "rgba(220,220,220,0.5)",
                strokeColor: "rgba(220,220,220,0.8)",
                highlightFill: "rgba(220,220,220,0.75)",
                highlightStroke: "rgba(220,220,220,1)",
                data: this.model.uploads
            },
            {
                label: "Downloads",
                fillColor: "rgba(151,187,205,0.5)",
                strokeColor: "rgba(151,187,205,0.8)",
                highlightFill: "rgba(151,187,205,0.75)",
                highlightStroke: "rgba(151,187,205,1)",
                data: this.model.downloads
            }
        ]};

        new Chart(ctx).Bar(data);

        return this;
    },

    className: 'stat-section'
});


window.App = Backbone.View.extend({
    initialize: function (){

        this.fetchData();
    },

    el: $("body"),

    statsListEl: $("#stat-sections-container"),

    fetchData: function(){
        var that = this;

        $.get( "statistics-data", function( data ) {

            var response = jQuery.parseJSON(data);

            that.statsListEl.empty();

            var trendView = new TrendView({model: response.trend})

            that.statsListEl.append(trendView.el);

            _.each(response.days, function(statDataItem){
                var view = new StatsView({model: statDataItem});

                that.statsListEl.append(view.el);
            });
        });
    }
});

$(document).ready(function(){
    window.App = new App();
});
