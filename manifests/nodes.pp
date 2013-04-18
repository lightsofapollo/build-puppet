# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

## relabs machines - check with dustin to borrow one

node "relabs02.build.mtv1.mozilla.com" {
}

node "relabs03.build.mtv1.mozilla.com" {
}

node "relabs04.build.mtv1.mozilla.com" {
}

node "relabs05.build.mtv1.mozilla.com" {
}

node "relabs06.build.mtv1.mozilla.com" {
    # in use by bhearsum
    include toplevel::server
}

node "relabs07.build.mtv1.mozilla.com" {
}

node "relabs08.build.mtv1.mozilla.com" {
}

## foopies

node /foopy\d+.build.mtv1.mozilla.com/ {
    include toplevel::server::foopy
}

node /foopy\d+.build.scl1.mozilla.com/ {
    include toplevel::server::foopy
}

node /foopy\d+.p\d+.releng.scl1.mozilla.com/ {
    include toplevel::server::foopy
}

## testers

node /talos-mtnlion-r5-\d+.test.releng.scl3.mozilla.com/ {
    include toplevel::slave::test::gpu
}

node /tst-.*\.build\.aws-.*\.mozilla\.com/ {
    # Make sure we get our /etc/hosts set up
    class {
        "network::aws": stage => network,
    }
    include toplevel::slave::test::headless
}

node /tst-.*\.test\.releng\.(use1|usw2)\.mozilla\.com/ {
    # Make sure we get our /etc/hosts set up
    class {
        "network::aws": stage => network,
    }
    include toplevel::slave::test::headless
}

node /talos-linux\d+-ix-\d+\.test\.releng\.scl3\.mozilla\.com/ {
    include toplevel::slave::test::gpu
}

## builders

node /linux64-ix-slave\d+.build.scl1.mozilla.com/ {
    include toplevel::slave::build::mock
}

node /bld-linux64-ix-\d+.build.(scl1|mtv1).mozilla.com/ {
    include toplevel::slave::build::mock
}

node /bld-centos6-hp-\d+.build.(scl1|mtv1).mozilla.com/ {
    include toplevel::slave::build::mock
}

node /(bld|try|dev)-.*\.build\.aws-.*\.mozilla\.com/ {
    # Make sure we get our /etc/hosts set up
    class {
        "network::aws": stage => network,
    }
    include toplevel::slave::build::mock
}

node /(bld|try|dev)-.*\.(build|try|dev)\.releng\.(use1|usw2)\.mozilla.com/ {
    # Make sure we get our /etc/hosts set up
    class {
        "network::aws": stage => network,
    }
    include toplevel::slave::build::mock
}


## puppetmasters

node /puppetmaster-\d+\..*\.aws-.*\.mozilla\.com/ {
    include toplevel::server::puppetmaster::standalone
}

## mozpool servers

node "mobile-imaging-stage1.p127.releng.scl1.mozilla.com" {
    $extra_root_keys = [ 'mcote' ]
    $is_bmm_admin_host = true
    $mozpool_staging = true
    include toplevel::server::mozpool
}

node /mobile-imaging-\d+\.p\d+\.releng\.scl1\.mozilla\.com/ {
    $extra_root_keys = [ 'mcote' ]
    $is_bmm_admin_host = $fqdn ? { /^mobile-imaging-001/ => true, default => false }
    $mozpool_staging = false
    include toplevel::server::mozpool
}

## buildbot masters

node "buildbot-master51.srv.releng.use1.mozilla.com" {
    buildmaster::buildbot_master {
        "bm51-tests1-linux":
            http_port => 8201,
            master_type => "tests",
            basedir => "tests1-linux";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master52.srv.releng.use1.mozilla.com" {
    buildmaster::buildbot_master {
        "bm52-tests1-linux":
            http_port => 8201,
            master_type => "tests",
            basedir => "tests1-linux";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master53.srv.releng.usw2.mozilla.com" {
    buildmaster::buildbot_master {
        "bm53-tests1-linux":
            http_port => 8201,
            master_type => "tests",
            basedir => "tests1-linux";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master54.srv.releng.usw2.mozilla.com" {
    buildmaster::buildbot_master {
        "bm54-tests1-linux":
            http_port => 8201,
            master_type => "tests",
            basedir => "tests1-linux";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master55.srv.releng.use1.mozilla.com" {
    buildmaster::buildbot_master {
        "bm55-try1":
            http_port => 8101,
            master_type => "try",
            basedir => "try1";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master56.srv.releng.usw2.mozilla.com" {
    buildmaster::buildbot_master {
        "bm56-try1":
            http_port => 8101,
            master_type => "try",
            basedir => "try1";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master57.srv.releng.use1.mozilla.com" {
    buildmaster::buildbot_master {
        "bm57-build1":
            http_port => 8001,
            master_type => "build",
            basedir => "build1";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master58.srv.releng.usw2.mozilla.com" {
    buildmaster::buildbot_master {
        "bm58-build1":
            http_port => 8001,
            master_type => "build",
            basedir => "build1";
    }
    include toplevel::server::buildmaster
}
node "buildbot-master59.srv.releng.use1.mozilla.com" {
    buildmaster::buildbot_master {
        "bm59-try1":
            http_port => 8101,
            master_type => "try",
            basedir => "try1";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master60.srv.releng.usw2.mozilla.com" {
    buildmaster::buildbot_master {
        "bm60-try1":
            http_port => 8101,
            master_type => "try",
            basedir => "try1";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master61.srv.releng.use1.mozilla.com" {
    buildmaster::buildbot_master {
        "bm61-build1":
            http_port => 8001,
            master_type => "build",
            basedir => "build1";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master62.srv.releng.use1.mozilla.com" {
    buildmaster::buildbot_master {
        "bm62-build1":
            http_port => 8001,
            master_type => "build",
            basedir => "build1";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master63.srv.releng.use1.mozilla.com" {
    buildmaster::buildbot_master {
        "bm63-build1":
            http_port => 8001,
            master_type => "build",
            basedir => "build1";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master64.srv.releng.usw2.mozilla.com" {
    buildmaster::buildbot_master {
        "bm64-build1":
            http_port => 8001,
            master_type => "build",
            basedir => "build1";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master65.srv.releng.usw2.mozilla.com" {
    buildmaster::buildbot_master {
        "bm65-build1":
            http_port => 8001,
            master_type => "build",
            basedir => "build1";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master66.srv.releng.usw2.mozilla.com" {
    buildmaster::buildbot_master {
        "bm66-build1":
            http_port => 8001,
            master_type => "build",
            basedir => "build1";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master67.srv.releng.use1.mozilla.com" {
    buildmaster::buildbot_master {
        "bm67-tests1-linux":
            http_port => 8201,
            master_type => "tests",
            basedir => "tests1-linux";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master68.srv.releng.usw2.mozilla.com" {
    buildmaster::buildbot_master {
        "bm68-tests1-linux":
            http_port => 8201,
            master_type => "tests",
            basedir => "tests1-linux";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master69.srv.releng.use1.mozilla.com" {
    buildmaster::buildbot_master {
        "bm69-tests1-windows":
            http_port => 8201,
            master_type => "tests",
            basedir => "tests1-windows";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master70.srv.releng.use1.mozilla.com" {
    buildmaster::buildbot_master {
        "bm70-tests1-windows":
            http_port => 8201,
            master_type => "tests",
            basedir => "tests1-windows";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master71.srv.releng.use1.mozilla.com" {
    buildmaster::buildbot_master {
        "bm71-tests1-windows":
            http_port => 8201,
            master_type => "tests",
            basedir => "tests1-windows";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master72.srv.releng.usw2.mozilla.com" {
    buildmaster::buildbot_master {
        "bm72-tests1-windows":
            http_port => 8201,
            master_type => "tests",
            basedir => "tests1-windows";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master73.srv.releng.usw2.mozilla.com" {
    buildmaster::buildbot_master {
        "bm73-tests1-windows":
            http_port => 8201,
            master_type => "tests",
            basedir => "tests1-windows";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master74.srv.releng.usw2.mozilla.com" {
    buildmaster::buildbot_master {
        "bm74-tests1-windows":
            http_port => 8201,
            master_type => "tests",
            basedir => "tests1-windows";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master75.srv.releng.use1.mozilla.com" {
    buildmaster::buildbot_master {
        "bm75-tests1-macosx":
            http_port => 8201,
            master_type => "tests",
            basedir => "tests1-macosx";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master76.srv.releng.use1.mozilla.com" {
    buildmaster::buildbot_master {
        "bm76-tests1-macosx":
            http_port => 8201,
            master_type => "tests",
            basedir => "tests1-macosx";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master77.srv.releng.use1.mozilla.com" {
    buildmaster::buildbot_master {
        "bm77-tests1-macosx":
            http_port => 8201,
            master_type => "tests",
            basedir => "tests1-macosx";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master78.srv.releng.usw2.mozilla.com" {
    buildmaster::buildbot_master {
        "bm78-tests1-macosx":
            http_port => 8201,
            master_type => "tests",
            basedir => "tests1-macosx";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master79.srv.releng.usw2.mozilla.com" {
    buildmaster::buildbot_master {
        "bm79-tests1-macosx":
            http_port => 8201,
            master_type => "tests",
            basedir => "tests1-macosx";
    }
    include toplevel::server::buildmaster
}

node "buildbot-master80.srv.releng.usw2.mozilla.com" {
    buildmaster::buildbot_master {
        "bm80-tests1-macosx":
            http_port => 8201,
            master_type => "tests",
            basedir => "tests1-macosx";
    }
    include toplevel::server::buildmaster
}
