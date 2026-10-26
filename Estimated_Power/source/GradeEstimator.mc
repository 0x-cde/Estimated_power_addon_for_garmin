import Toybox.Lang;

//! Road gradient from altitude vs distance. Connect IQ does not expose the
//! device's own grade value, so it is derived here with a least-squares fit
//! over the most recent stretch of road. A distance-based window (not a time
//! window) keeps the barometer's ~0.1-0.3 m noise from dominating at low speed
//! and keeps lag short at high speed.
class GradeEstimator {

    private const SIZE = 30;          // buffer capacity in samples
    private const MIN_SPAN_M = 25.0;  // shortest road length to fit over
    private const MIN_SAMPLES = 4;
    private const MIN_STEP_M = 0.5;   // ignore samples while (nearly) stopped
    private const MAX_GRADE = 0.30;

    private var _dist as Array<Float>;
    private var _alt as Array<Float>;
    private var _head as Number = 0;
    private var _count as Number = 0;
    private var _grade as Float = 0.0;

    function initialize() {
        _dist = new Array<Float>[SIZE];
        _alt = new Array<Float>[SIZE];
        reset();
    }

    function reset() as Void {
        for (var i = 0; i < SIZE; i++) {
            _dist[i] = 0.0;
            _alt[i] = 0.0;
        }
        _head = 0;
        _count = 0;
        _grade = 0.0;
    }

    //! Grade as a fraction (0.05 = 5 %). Holds the last value while stopped.
    function getGrade() as Float {
        return _grade;
    }

    function addSample(distanceM as Float, altitudeM as Float) as Void {
        if (_count > 0) {
            var last = _dist[(_head - 1 + SIZE) % SIZE];
            if (distanceM < last - 1.0) {
                // Distance went backwards: activity was reset.
                reset();
            } else if (distanceM - last < MIN_STEP_M) {
                return;
            }
        }

        _dist[_head] = distanceM;
        _alt[_head] = altitudeM;
        _head = (_head + 1) % SIZE;
        if (_count < SIZE) {
            _count++;
        }
        fit();
    }

    private function fit() as Void {
        var newest = _dist[(_head - 1 + SIZE) % SIZE];

        // Walk back until the window covers enough road.
        var n = 0;
        var enough = false;
        for (var i = 1; i <= _count; i++) {
            n = i;
            var idx = (_head - i + SIZE) % SIZE;
            if (newest - _dist[idx] >= MIN_SPAN_M && n >= MIN_SAMPLES) {
                enough = true;
                break;
            }
        }
        if (!enough) {
            return;
        }

        var meanD = 0.0;
        var meanH = 0.0;
        for (var i = 1; i <= n; i++) {
            var idx = (_head - i + SIZE) % SIZE;
            meanD += _dist[idx];
            meanH += _alt[idx];
        }
        meanD /= n;
        meanH /= n;

        var sxy = 0.0;
        var sxx = 0.0;
        for (var i = 1; i <= n; i++) {
            var idx = (_head - i + SIZE) % SIZE;
            var dx = _dist[idx] - meanD;
            sxy += dx * (_alt[idx] - meanH);
            sxx += dx * dx;
        }
        if (sxx <= 0.0) {
            return;
        }

        var g = sxy / sxx;
        if (g > MAX_GRADE) {
            g = MAX_GRADE;
        } else if (g < -MAX_GRADE) {
            g = -MAX_GRADE;
        }
        _grade = g;
    }
}
