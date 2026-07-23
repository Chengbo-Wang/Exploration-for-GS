/**
 * Escaping the Blur Trap — Academic Project Page
 * Main JavaScript entry point.
 */

document.addEventListener('DOMContentLoaded', function () {
    // Render LaTeX math expressions throughout the page using KaTeX.
    if (typeof renderMathInElement !== 'undefined') {
        renderMathInElement(document.body, {
            delimiters: [
                { left: '$$', right: '$$', display: true },
                { left: '$',  right: '$',  display: false }
            ]
        });
    }

    // Canvas image comparison (based on EDGS video_comparison.js)
    var canvas = document.getElementById('comp-canvas');
    if (canvas) {
        var ctx = canvas.getContext('2d');
        var position = 0.5;
        var leftImg = new Image(), rightImg = new Image();
        var leftLoaded = false, rightLoaded = false;
        var leftLabel = 'Ours', rightLabel = '3DGS';

        function loadImages(lSrc, rSrc) {
            leftLoaded = rightLoaded = false;
            leftImg.src = lSrc; rightImg.src = rSrc;
        }
        function draw() {
            if (!leftLoaded || !rightLoaded) return;
            var w = leftImg.naturalWidth, h = leftImg.naturalHeight;
            canvas.width = w; canvas.height = h;

            // Draw left image
            ctx.drawImage(leftImg, 0, 0, w, h);

            // Draw right image (reveal from split position)
            var splitX = w * position;
            ctx.drawImage(rightImg, splitX, 0, w - splitX, h, splitX, 0, w - splitX, h);

            // --- Divider line (matches EDGS: #AAAAAA, lineWidth 5) ---
            ctx.beginPath();
            ctx.moveTo(splitX, 0);
            ctx.lineTo(splitX, h);
            ctx.closePath();
            ctx.strokeStyle = '#AAAAAA';
            ctx.lineWidth = 5;
            ctx.stroke();

            // --- Arrow handle (matches EDGS exactly) ---
            var arrowLen = 0.09 * h;
            var arrowHeadW = 0.025 * h;
            var arrowHeadL = 0.04 * h;
            var arrowY = h * 0.8;
            var arrowW = 0.007 * h;
            var cx = splitX;

            // Circle background (warm yellow, EDGS: #FFD79340)
            ctx.beginPath();
            ctx.arc(cx, arrowY, arrowLen * 0.7, 0, Math.PI * 2);
            ctx.fillStyle = '#FFD79340'; ctx.fill();

            // Arrow body
            ctx.beginPath();
            ctx.moveTo(cx - arrowLen/2,              arrowY - arrowW/2);
            ctx.lineTo(cx + arrowLen/2 - arrowHeadL/2, arrowY - arrowW/2);
            // Right head
            ctx.lineTo(cx + arrowLen/2 - arrowHeadL/2, arrowY - arrowHeadW/2);
            ctx.lineTo(cx + arrowLen/2,                arrowY);
            ctx.lineTo(cx + arrowLen/2 - arrowHeadL/2, arrowY + arrowHeadW/2);
            ctx.lineTo(cx + arrowLen/2 - arrowHeadL/2, arrowY + arrowW/2);
            // Back
            ctx.lineTo(cx - arrowLen/2 + arrowHeadL/2, arrowY + arrowW/2);
            // Left head
            ctx.lineTo(cx - arrowLen/2 + arrowHeadL/2, arrowY + arrowHeadW/2);
            ctx.lineTo(cx - arrowLen/2,                arrowY);
            ctx.lineTo(cx - arrowLen/2 + arrowHeadL/2, arrowY - arrowHeadW/2);
            ctx.lineTo(cx - arrowLen/2 + arrowHeadL/2, arrowY);
            ctx.lineTo(cx - arrowLen/2 + arrowHeadL/2, arrowY - arrowW/2);
            ctx.lineTo(cx,                             arrowY - arrowW/2);
            ctx.closePath();
            ctx.fillStyle = '#AAAAAA'; ctx.fill();

            // Labels — colors match the method selector buttons
            ctx.font = '600 32px Poppins, Arial, sans-serif';
            ctx.shadowColor = 'rgba(0,0,0,0.4)';
            ctx.shadowBlur = 4;
            ctx.textBaseline = 'bottom';
            ctx.fillStyle = '#daa0aa';
            ctx.fillText(leftLabel, 12, h - 10);
            ctx.textAlign = 'right';
            ctx.fillStyle = '#8eb8d5';
            ctx.fillText(rightLabel, w - 12, h - 10);
            ctx.textAlign = 'left';
            ctx.shadowBlur = 0;
        }

        leftImg.onload = function () { leftLoaded = true; draw(); };
        rightImg.onload = function () { rightLoaded = true; draw(); };

        function update(e) {
            var r = canvas.getBoundingClientRect();
            var x = e.touches ? e.touches[0].clientX : e.clientX;
            position = Math.max(0, Math.min(1, (x - r.left) / r.width));
            draw();
        }

        canvas.addEventListener('mousedown', function (e) { update(e); });
        canvas.addEventListener('mousemove', function (e) { if (e.buttons) update(e); });
        canvas.addEventListener('touchstart', function (e) { update(e); });
        canvas.addEventListener('touchmove', function (e) { update(e); });
        window.addEventListener('resize', draw);

        // Current selections — initialized from the active scene button
        var activeSceneBtn = document.querySelector('.comp-scene-btn.active');
        var currentFrame = activeSceneBtn ? activeSceneBtn.dataset.frame : '00020';
        var leftMethod = 'Ours', rightMethod = '3DGS';

        function method2path(method) {
            var prefixes = { 'Ours': 'SS', 'GT': 'GT', 'HoGS': 'HoGS', '3DGS': '3DGS' };
            return 'assets/vis/' + prefixes[method] + '_' + currentFrame + '.png';
        }

        function reloadCanvas() {
            leftLabel = leftMethod; rightLabel = rightMethod;
            loadImages(method2path(leftMethod), method2path(rightMethod));
        }

        // Scene switcher buttons
        document.querySelectorAll('.comp-scene-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                document.querySelectorAll('.comp-scene-btn').forEach(function (b) { b.classList.remove('active'); });
                btn.classList.add('active');
                currentFrame = btn.dataset.frame;
                reloadCanvas();
            });
        });

        // Image switcher buttons
        document.querySelectorAll('.comp-btns').forEach(function (group) {
            var side = group.dataset.side;
            group.querySelectorAll('.comp-btn').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    group.querySelectorAll('.comp-btn').forEach(function (b) { b.classList.remove('active'); });
                    btn.classList.add('active');
                    if (side === 'left') { leftMethod = btn.dataset.method; }
                    else                 { rightMethod = btn.dataset.method; }
                    reloadCanvas();
                });
            });
        });

        // Initial load — use the frame from the active scene button
        reloadCanvas();
    }
});

/**
 * Copy BibTeX content to clipboard.
 */
function copyBibtex(btn) {
    const pre = document.getElementById('bibtex-content');
    if (!pre) return;
    navigator.clipboard.writeText(pre.textContent).then(() => {
        btn.textContent = '✓ Copied!';
        btn.classList.add('copied');
        setTimeout(() => {
            btn.textContent = '📋 Copy';
            btn.classList.remove('copied');
        }, 2000);
    });
}
