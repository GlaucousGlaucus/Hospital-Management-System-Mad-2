const gulp = require('gulp');
const browserSync = require('browser-sync').create();
const paths = {
    python: ['**/*.py'],
    html: ['templates/**/*.html'],
    css: ['static/**/*.css'],
    js: ['static/**/*.js']
};

function initBrowserSync(cb) {
    browserSync.init({
        proxy: 'http://localhost:5000',
        port: 5001,
        open: false,
        injectChanges: true,
        notify: false,
        reloadOnRestart: true,
        files: [
            'templates/**/*.html',
            'static/**/*.css',
            'static/**/*.js',
            '**/*.py'
        ],
    });
    cb();
}

exports.default = gulp.series(initBrowserSync);
