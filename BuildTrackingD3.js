const fs = require('fs');
const { JSDOM } = require('jsdom');
const { Octokit } = require('@octokit/rest');
const { DateTime } = require("luxon");

const owner = 'owner'; // replace owner of repo
const repo = 'repo'; // replace with owner name
const branch = 'branch'; // replace with branch name
const token = 'token'; // replace with GitHub token
const n = 30; // replace with the number of commits you want to fetch

const octokit = new Octokit({
  auth: token,
});

function formatDate(date, n) {
  // Parse the timestamp and convert it to the desired timezone
  const commitTime = DateTime.fromISO(date, { zone: 'utc' });
  const commitTimeLocal = commitTime.setZone('Europe/Berlin');

  if (n >= 30) {
    return commitTimeLocal.toFormat('dd.MM.\HH:mm');
  } else {
    return commitTimeLocal.toFormat('dd.MM.yyyy \n HH:mm');
  }
}

async function getImageData(commitSha) {
  const octokit = new Octokit({
    auth: `token ${token}`,
  });

  try {
    // Get the reference SHA
    const refResponse = await octokit.git.getRef({
      owner,
      repo: repo,
      ref: `graalvm-metrics/${commitSha}`,
    });
    const refSha = refResponse.data.object.sha;

    console.log(refSha)

    // Get the tree SHA
    const treeResponse = await octokit.git.getTree({
      owner,
      repo: repo,
      tree_sha: refSha,
    });
    const blobSha = treeResponse.data.tree[0].sha;

    // Get the blob content
    const blobResponse = await octokit.git.getBlob({
      owner,
      repo: repo,
      file_sha: blobSha,
    });

    const content = Buffer.from(blobResponse.data.content, 'base64').toString('utf-8');
    const data = JSON.parse(content);

    console.log(data.image_details.total_bytes / 1e6)

    return [
      data.image_details.total_bytes / 1e6,
      data.image_details.code_area.bytes / 1e6,
      data.image_details.image_heap.bytes / 1e6,
    ];
  } catch (error) {
    console.error('Error fetching image data:', error.message);
    return [0, 0, 0];
  }
}

// Function to fetch data
async function fetchData() {
  return new Promise(async (resolve, reject) => {

    const response = await octokit.request('https://api.github.com/repos/' + owner + '/' + repo + '/events', {
      headers: {
          "Authorization": "Bearer " + token
      }
    });

    // get push events
    var pushEvents = await getPushEvents(response);

    // Prepare data
    const timestamps = [];
    const shas = [];

    for (const pushEvent of pushEvents) {
      timestamps.push(pushEvent.created_at);
      shas.push(pushEvent.payload.commits[pushEvent.payload.commits.length - 1].sha);
    }

    // Extract data for plotting
    const commitDates = timestamps.map(timestamp => formatDate(timestamp, n));
    const imageDataPromises = shas.map(async sha => await getImageData(sha));
    const imageData = await Promise.all(imageDataPromises);
    const imageSizes = imageData.filter(entry => entry !== 0).map(entry => entry[0]);
    const codeAreaSizes = imageData.filter(entry => entry !== 0).map(entry => entry[1]);
    const imageHeapSizes = imageData.filter(entry => entry !== 0).map(entry => entry[2]);

    const data= {
      commitDates: commitDates,
      imageData: imageData,
      imageSizes: imageSizes,
      codeAreaSizes: codeAreaSizes,
      imageHeapSizes: imageHeapSizes
    }

    resolve(data);
  });
}

async function getPushEvents(response) {
  const eventsArray = response.data;
  var linkHeader = response.headers.link;
  const nextPageMatch = linkHeader.match(/<([^>]+)>;\s*rel="next"/);
  var commitsLeft = n;
  var pushEvents = [];

  for (const event of eventsArray) {
    if (commitsLeft <= 0) {
      break;
    }
    if (event.type === "PushEvent" && event.payload.ref === `refs/heads/${branch}`) {
      pushEvents.push(event);
      commitsLeft -= 1;
    }
  }

  while (linkHeader && linkHeader.includes('rel="next"') && commitsLeft > 0) {
    // Extract the URL for the next page
    const nextPageMatch = linkHeader.match(/<([^>]+)>;\s*rel="next"/);
    const nextPageUrl = nextPageMatch ? nextPageMatch[1] : null;

    // Make the request for the next page
    const response = await fetch(nextPageUrl, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const responseJson = await response.json();

    for (const event of responseJson) {
      if (commitsLeft <= 0) {
        break;
      }
      if (event.type === "PushEvent" && event.payload.ref === `refs/heads/${branch}`) {
        pushEvents.push(event);
        commitsLeft -= 1;
      }
    }

    // Update linkHeader for the next iteration
    linkHeader = response.headers.get("link");
  }
  return pushEvents;
}

async function createChart() {
  try {
    // Use dynamic import for d3
    const d3 = await import('d3');
    const data = await fetchData();
    const labels = data.commitDates.reverse();
    const datasets = [
      {
        label: 'Image Sizes',
        data: data.imageSizes.reverse(),
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
      },
      {
        label: 'Code Area Sizes',
        data: data.codeAreaSizes.reverse(),
        borderColor: 'rgba(255, 99, 132, 1)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
      },
      {
        label: 'Image Heap Sizes',
        data: data.imageHeapSizes.reverse(),
        borderColor: 'rgba(255, 205, 86, 1)',
        backgroundColor: 'rgba(255, 205, 86, 0.2)',
      },
    ];

    // Use JSDOM to create a virtual DOM
    const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>');
    global.document = dom.window.document;

    const svgWidth = 800;
    const svgHeight = 400;

    const margin = { top: 20, right: 20, bottom: 60, left: 50 };
    const width = svgWidth - margin.left - margin.right;
    const height = svgHeight - margin.top - margin.bottom;

    const xScale = d3.scaleBand().domain(labels).range([0, width]).padding(0.1);
    const yScale = d3.scaleLinear().domain([0, d3.max(data.imageSizes)]).range([height, 0]);

    const svg = d3.select('body')
      .append('svg')
      .attr('width', svgWidth)
      .attr('height', svgHeight);

    const chart = svg.append('g')
      .attr('transform', `translate(${margin.left}, ${margin.top})`);

    // Add dashed grid lines for the x-axis
    chart.append('g')
      .attr('class', 'grid')
      .attr('transform', `translate(0, ${height})`)
      .call(
        d3.axisBottom(xScale)
          .tickSize(-height)
          .tickFormat('')
          .tickSizeOuter(0)
      )
      .selectAll('.tick line')
      .attr('stroke', 'lightgrey') // Adjust color as needed
      .attr('stroke-dasharray', '2,2') // Adjust dash pattern as needed
      .attr('stroke-width', 1); // Adjust line thickness as needed

    // Add dashed grid lines for the y-axis
    chart.append('g')
      .attr('class', 'grid')
      .call(
        d3.axisLeft(yScale)
          .tickSize(-width)
          .tickFormat('')
          .tickSizeOuter(0)
      )
      .selectAll('.tick line')
      .attr('stroke', 'lightgrey') // Adjust color as needed
      .attr('stroke-dasharray', '2,2') // Adjust dash pattern as needed
      .attr('stroke-width', 1); // Adjust line thickness as needed

    chart.append('g')
      .attr('transform', `translate(0, ${height})`)
      .call(d3.axisBottom(xScale))
      .selectAll('text')
      .style('text-anchor', 'end')
      .attr('transform', 'rotate(-45)');

    chart.append('g')
      .call(d3.axisLeft(yScale));

    datasets.forEach(dataset => {
      // Connect data points with lines
      chart.append('path')
        .datum(dataset.data)
        .attr('fill', 'none')
        .attr('stroke', dataset.borderColor)
        .attr('stroke-width', 2)
        .attr('d', d3.line()
          .x((d, i) => xScale(labels[i]) + xScale.bandwidth() / 2)
          .y(d => yScale(d))
        );

      // Add circles at data points for each dataset
      chart.selectAll(`circle.${dataset.label}`)
        .data(dataset.data)
        .enter().append('circle')
        .attr('class', dataset.label) // Ensure unique class for each dataset
        .attr('cx', (d, i) => xScale(labels[i]) + xScale.bandwidth() / 2)
        .attr('cy', d => yScale(d))
        .attr('r', 5)
        .attr('fill', dataset.borderColor);
    });

    // Save the SVG as a file
    fs.writeFileSync('output_point_plot.svg', d3.select('body').html());
    console.log('The point plot SVG file was created.');
  } catch (error) {
    console.error('Error fetching data:', error);
  }
}

// Call the createChart function
createChart();