# until we get a moment for some real CI
echo "start"
for image in 'dungeontimes-d-api' 'dungeontimes-d-dm' 'dungeontimes-d-web' 'dungeontimes-d-rabbit'; do
    echo '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
    echo $image
    docker tag $image lobachevsky.net:4444/dungeon_times/$image:latest
    docker push lobachevsky.net:4444/dungeon_times/$image:latest
done
