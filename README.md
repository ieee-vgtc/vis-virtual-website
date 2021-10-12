## Welcome to IEEE VIS 2020 Virtual!
<div class="embed-responsive embed-responsive-16by9 mb-4">
<iframe class="" width="560" height="315" src="https://www.youtube-nocookie.com/embed/TRVB7399ynY?rel=0" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
</div>

### Social Media

Please feel free to use social media to talk about [IEEE VIS 2020](http://ieeevis.org/year/2020/welcome).
Enjoy the 2020 edition of <strong>#ieeevis</strong>.

### Help

Feel free to visit [our Help page above](/help.html) for answers to common questions, where we also have a short tutorial on using Discord.  If you are still having issues, feel free to ask in #support in Discord or e-mail web@ieeevis.org.

### Installation

See the `Makefile` for build scripts.  Generally, to run it locally, use `make run`.

For **streaming**, we have a simple shell script that copies assets from the separate [ieeevisstreaming](https://github.com/michaschwab/ieeevisstreaming) repo, which is included in a submodule.  If you want to update the streaming assets, please first update that repository, then update the submodule with `git submodule update --init --recursive
`.  Then run the script `scripts/copy_streaming_assets.sh`, which will copy in files from that submodule and rename things/fix links.  See the script opening comments for typical usage.

### Acknowledgements

The IEEE VIS 2020 Virtual site was adapted from the MiniConf software by the [IEEE VIS 2020 website, technology, and archive commmittees](http://ieeevis.org/year/2020/info/committees/conference-committee) with content input from [all conference committees](http://ieeevis.org/year/2020/info/committees/conference-committee).

MiniConf was originally built by [Hendrik Strobelt](http://twitter.com/hen_str) and [Sasha Rush](http://twitter.com/srush_nlp); you can find [the original open-source implementation on GitHub](https://github.com/Mini-Conf/Mini-Conf), and [our fork as well](https://github.com/ieee-vgtc/vis-virtual-website) (which will become public after the conclusion of the conference).

We welcome your comments about your experience and anything we can do to make your virtual experience better.  Please join us in #support or #suggestions on Discord, or feel free to e-mail the committees directly.
