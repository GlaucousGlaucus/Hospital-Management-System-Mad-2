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
        reloadDebounce: 500,  // short delay between changes
        reloadDelay: 0,       // start reloading immediately
        reloadThrottle: 0,    // don’t throttle reloads
    });
    cb();
}

gulp.task('sass', function() {
    return gulp.src("app/scss/*.scss")
        .pipe(sass())                      // compile SASS → CSS
        .pipe(gulp.dest("app/css"))        // write to disk
        .pipe(browserSync.stream({match: '**/*.css'})); // inject updated CSS live
});

exports.default = gulp.series(initBrowserSync);
