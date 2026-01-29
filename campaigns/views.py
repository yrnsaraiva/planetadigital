from django.shortcuts import render

from .models import Campaign


def list_campaigns(request):
    campaigns = Campaign.objects.all()
    context = {'campaigns': campaigns}

    return render(request, 'campaigns/campaign.html', context=context)


def campaign_detail(request, slug):
    campaign = Campaign.objects.get(slug=slug)
    context = {'campaign': campaign}

    return render(request, 'campaigns/campaign_detail.html', context=context)